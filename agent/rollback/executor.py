"""Deterministic Rollback Executor and EventBus Coordinator."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from agent.execution.filesystem import FilesystemSandboxDriver
from agent.execution.git_worktree import GitWorktreeDriver
from agent.rollback.dag import RollbackDAGManager
from agent.rollback.planner import RollbackPlan, RollbackPlanner, RollbackStrategy
from agent.rollback.verifier import RollbackVerificationResult, RollbackVerifier
from agent.runtime.checkpoint import CheckpointManager, CheckpointRecord, WorkspaceStateHasher
from agent.runtime.event_bus import EventType, RuntimeEventBus


class RollbackExecutorSummary(BaseModel):
    """Final summary outcome of a rollback execution operation."""

    rollback_plan_id: str
    session_id: str
    target_step_index: int
    status: str = Field(..., description="RESTORED, PARTIALLY_RESTORED, FAILED, or SKIPPED_ALREADY_AT_TARGET")
    reverted_action_ids: List[str] = Field(default_factory=list)
    failed_action_id: Optional[str] = None
    verification_result: Optional[RollbackVerificationResult] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class RollbackExecutor:
    """Orchestrates deterministic rollback execution across Drivers, Checkpoints, and EventBus."""

    def __init__(
        self,
        dag_manager: RollbackDAGManager,
        checkpoint_manager: CheckpointManager,
        event_bus: RuntimeEventBus,
        fs_driver: Optional[FilesystemSandboxDriver] = None,
        git_driver: Optional[GitWorktreeDriver] = None,
        verifier: Optional[RollbackVerifier] = None,
    ) -> None:
        self.dag_manager = dag_manager
        self.checkpoint_manager = checkpoint_manager
        self.event_bus = event_bus
        self.fs_driver = fs_driver or FilesystemSandboxDriver()
        self.git_driver = git_driver or GitWorktreeDriver()
        self.verifier = verifier or RollbackVerifier(self.fs_driver, self.git_driver)
        self.planner = RollbackPlanner(dag_manager, checkpoint_manager)

    async def execute_rollback_to_step(
        self,
        session_id: str,
        target_step_index: int,
        workspace_root: str,
        current_git_hash: Optional[str] = None,
        current_fs_hash: Optional[str] = None,
    ) -> RollbackExecutorSummary:
        """Execute a deterministic rollback plan to target_step_index.
        
        Enforces:
        - Idempotency (ADR-008): Skips if workspace is already at target state.
        - Reverse topological DAG order execution.
        - Non-LLM inverse/snapshot driver invocation.
        - EventBus telemetry streaming.
        - Post-restoration verification assertions.
        """
        # 1. Emit ROLLBACK_REQUESTED event
        await self.event_bus.publish(
            event_type=EventType.ROLLBACK_REQUESTED,
            session_id=session_id,
            payload={"target_step_index": target_step_index},
        )

        # 2. Query target checkpoint
        checkpoints = self.checkpoint_manager.list_checkpoints(session_id)
        target_chk: Optional[CheckpointRecord] = None
        for chk in checkpoints:
            if chk.step_index == target_step_index:
                target_chk = chk
                break

        # 3. Idempotency Check (ADR-008)
        if target_chk:
            current_hash = WorkspaceStateHasher.compute_hash(
                git_ref=current_git_hash or target_chk.git_state_ref,
                fs_ref=current_fs_hash or target_chk.filesystem_state_ref,
                db_ref=target_chk.postgresql_state_ref,
                extra_metadata=target_chk.metadata,
            )
            if current_hash == target_chk.integrity_hash and current_git_hash is not None and current_fs_hash is not None:
                summary = RollbackExecutorSummary(
                    rollback_plan_id="idempotent_skip",
                    session_id=session_id,
                    target_step_index=target_step_index,
                    status="SKIPPED_ALREADY_AT_TARGET",
                    error_message="Workspace is already at target checkpoint state.",
                )
                await self.event_bus.publish(
                    event_type=EventType.ROLLBACK_COMPLETED,
                    session_id=session_id,
                    payload=summary.model_dump(),
                )
                return summary

        # 4. Construct Rollback Plan
        plan: RollbackPlan = self.planner.build_plan_for_step(session_id, target_step_index)
        await self.event_bus.publish(
            event_type=EventType.ROLLBACK_PLANNED,
            session_id=session_id,
            payload=plan.model_dump(),
        )

        # 5. Start Rollback Execution
        await self.event_bus.publish(
            event_type=EventType.ROLLBACK_STARTED,
            session_id=session_id,
            payload={"plan_id": plan.rollback_plan_id, "total_steps": len(plan.execution_steps)},
        )

        reverted_action_ids: List[str] = []
        failed_action_id: Optional[str] = None

        # 6. Execute Reverse Topological Steps
        for step_item in plan.execution_steps:
            await self.event_bus.publish(
                event_type=EventType.ROLLBACK_ACTION_STARTED,
                session_id=session_id,
                action_id=step_item.action_id,
                payload=step_item.model_dump(),
            )

            try:
                success = False
                if step_item.strategy == RollbackStrategy.INVERSE_OPERATION and step_item.inverse_recipe:
                    recipe = step_item.inverse_recipe
                    if recipe.inverse_tool_name == "fs.delete_file":
                        res = self.fs_driver.delete_file(recipe.arguments["path"], workspace_root)
                        success = res.success
                    elif recipe.inverse_tool_name == "fs.restore_preimage":
                        success = self.fs_driver.restore_preimage(
                            recipe.arguments["path"],
                            recipe.arguments.get("preimage_hash"),
                            workspace_root,
                        )
                    elif recipe.inverse_tool_name == "fs.move_file":
                        res = self.fs_driver.move_file(
                            recipe.arguments["source_path"],
                            recipe.arguments["destination_path"],
                            workspace_root,
                        )
                        success = res.success
                elif step_item.strategy == RollbackStrategy.GIT_WORKTREE_CHECKOUT and step_item.git_commit_hash:
                    success = self.git_driver.restore_commit_snapshot(workspace_root, step_item.git_commit_hash)
                elif step_item.strategy == RollbackStrategy.FILESYSTEM_PREIMAGE_RESTORE:
                    success = True  # Handled via preimages

                if not success:
                    failed_action_id = step_item.action_id
                    break

                reverted_action_ids.append(step_item.action_id)
                await self.event_bus.publish(
                    event_type=EventType.ROLLBACK_ACTION_COMPLETED,
                    session_id=session_id,
                    action_id=step_item.action_id,
                    payload={"status": "SUCCESS"},
                )
            except Exception as err:
                failed_action_id = step_item.action_id
                await self.event_bus.publish(
                    event_type=EventType.ROLLBACK_ACTION_FAILED,
                    session_id=session_id,
                    action_id=step_item.action_id,
                    payload={"error": str(err)},
                )
                break

        # 7. Partial Restoration Handling
        if failed_action_id is not None:
            summary = RollbackExecutorSummary(
                rollback_plan_id=plan.rollback_plan_id,
                session_id=session_id,
                target_step_index=target_step_index,
                status="PARTIALLY_RESTORED" if reverted_action_ids else "FAILED",
                reverted_action_ids=reverted_action_ids,
                failed_action_id=failed_action_id,
                error_message=f"Rollback halted on action '{failed_action_id}'",
            )
            await self.event_bus.publish(
                event_type=EventType.ROLLBACK_FAILED,
                session_id=session_id,
                payload=summary.model_dump(),
            )
            return summary

        # 8. Post-Rollback Verification Suite
        ver_result: Optional[RollbackVerificationResult] = None
        if target_chk:
            ver_result = self.verifier.verify_rollback(
                workspace_root=workspace_root,
                target_checkpoint=target_chk,
            )

        final_status = "RESTORED" if (ver_result is None or ver_result.passed) else "VERIFICATION_FAILED"

        summary = RollbackExecutorSummary(
            rollback_plan_id=plan.rollback_plan_id,
            session_id=session_id,
            target_step_index=target_step_index,
            status=final_status,
            reverted_action_ids=reverted_action_ids,
            verification_result=ver_result,
        )

        await self.event_bus.publish(
            event_type=EventType.ROLLBACK_COMPLETED,
            session_id=session_id,
            payload=summary.model_dump(),
        )

        return summary
