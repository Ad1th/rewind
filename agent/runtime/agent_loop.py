"""Agent Runtime Execution Loop Orchestrator."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.db.repositories import PersistenceRepository
from agent.execution.filesystem import FilesystemSandboxDriver
from agent.execution.git_worktree import GitWorktreeDriver
from agent.execution.postgres import PostgresRollbackDriver
from agent.llm.provider import LLMProvider
from agent.rollback.dag import RollbackDAGManager
from agent.runtime.checkpoint import CheckpointManager, CheckpointRecord
from agent.runtime.contracts import Action, ActionProposal, ActionResult, ActionStatus
from agent.runtime.event_bus import EventType, RuntimeEventBus
from agent.runtime.interceptor import ActionInterceptor
from agent.security.policy import PolicyEngine
from agent.security.risk import RiskEngine
from agent.tools.registry import ToolRegistry


class StepExecutionResult(BaseModel):
    step_index: int
    proposal: ActionProposal
    accepted: bool
    action: Optional[Action] = None
    result: Optional[ActionResult] = None
    rejection_reason: Optional[str] = None
    requires_approval: bool = False

    model_config = ConfigDict(frozen=True)


class AgentLoop:
    """Orchestrates the full step execution pipeline:
    LLM Proposal -> Interceptor -> Policy -> Risk -> Checkpoint -> Tool Execution -> EventBus -> Persistence.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        policy_engine: PolicyEngine,
        risk_engine: RiskEngine,
        checkpoint_manager: CheckpointManager,
        dag_manager: RollbackDAGManager,
        event_bus: RuntimeEventBus,
        llm_provider: LLMProvider,
        repo: Optional[PersistenceRepository] = None,
        fs_driver: Optional[FilesystemSandboxDriver] = None,
        git_driver: Optional[GitWorktreeDriver] = None,
        db_driver: Optional[PostgresRollbackDriver] = None,
    ) -> None:
        self.registry = registry
        self.policy_engine = policy_engine
        self.risk_engine = risk_engine
        self.checkpoint_manager = checkpoint_manager
        self.dag_manager = dag_manager
        self.event_bus = event_bus
        self.llm_provider = llm_provider
        self.repo = repo or PersistenceRepository()
        self.fs_driver = fs_driver or FilesystemSandboxDriver()
        self.git_driver = git_driver or GitWorktreeDriver()
        self.db_driver = db_driver or PostgresRollbackDriver()
        self.interceptor = ActionInterceptor(registry, policy_engine, risk_engine)
        self.step_counter: Dict[str, int] = {}

    async def execute_step(
        self,
        session_id: str,
        goal_prompt: str,
        workspace_root: str,
        active_permissions: Optional[List[str]] = None,
    ) -> Optional[StepExecutionResult]:
        """Execute a single cycle of the Agent Runtime loop."""
        current_step = self.step_counter.get(session_id, 0) + 1
        self.step_counter[session_id] = current_step

        # 1. Query LLM Provider for proposals
        history: List[Dict[str, Any]] = []
        proposals = await self.llm_provider.generate_proposals(session_id, goal_prompt, history)
        if not proposals:
            return None

        proposal = proposals[0]

        # 2. Intercept Proposal
        interception = self.interceptor.intercept_proposal(
            proposal=proposal,
            step_index=current_step,
            workspace_root=workspace_root,
            active_permissions=active_permissions or ["workspace.write", "workspace.read", "db.write", "net.http"],
        )

        if not interception.accepted or not interception.action:
            await self.event_bus.publish(
                event_type=EventType.ACTION_FAILED,
                session_id=session_id,
                payload={"reason": interception.rejection_reason},
            )
            return StepExecutionResult(
                step_index=current_step,
                proposal=proposal,
                accepted=False,
                rejection_reason=interception.rejection_reason,
            )

        action = interception.action

        # Handle Human Approval requirement for Risky/Irreversible actions
        if interception.requires_approval:
            await self.event_bus.publish(
                event_type=EventType.RISK_ASSESSED,
                session_id=session_id,
                action_id=action.action_id,
                payload={"requires_approval": True, "risk_score": action.risk_assessment.score},
            )
            await self.repo.save_action(action)
            return StepExecutionResult(
                step_index=current_step,
                proposal=proposal,
                accepted=True,
                action=action,
                requires_approval=True,
            )

        # 3. Create Pre-Execution Checkpoint
        pre_hash, exists = None, False
        if action.tool_name.startswith("fs."):
            target_p = str(action.arguments.get("path", action.arguments.get("source_path", "")))
            if target_p:
                pre_hash, exists = self.fs_driver.capture_preimage(target_p, workspace_root)

        chk: CheckpointRecord = await self.checkpoint_manager.create_checkpoint(
            session_id=session_id,
            workspace_id="ws-active",
            step_index=current_step,
            workspace_root=workspace_root,
            trigger_action_id=action.action_id,
        )
        await self.repo.save_checkpoint(chk)

        # 4. Generate Inverse Recipe & Execute Tool in Sandbox Driver
        inv_ref = None
        action_res: ActionResult = ActionResult(success=False, error_message="Execution skipped")

        if action.tool_name == "fs.create_file":
            action_res = self.fs_driver.create_file(action.arguments["path"], action.arguments.get("content", ""), workspace_root)
            inv_ref = self.fs_driver.generate_inverse_recipe("fs.create_file", action.arguments, pre_hash, exists)
        elif action.tool_name == "fs.write_file":
            action_res = self.fs_driver.write_file(action.arguments["path"], action.arguments.get("content", ""), workspace_root)
            inv_ref = self.fs_driver.generate_inverse_recipe("fs.write_file", action.arguments, pre_hash, exists)
        elif action.tool_name == "fs.delete_file":
            action_res = self.fs_driver.delete_file(action.arguments["path"], workspace_root)
            inv_ref = self.fs_driver.generate_inverse_recipe("fs.delete_file", action.arguments, pre_hash, exists)
        elif action.tool_name == "db.insert":
            action_res, preimage_id = self.db_driver.insert_row(
                action.arguments["table_name"], action.arguments["primary_key"], action.arguments["row_data"]
            )
            inv_ref = self.db_driver.generate_inverse_recipe("INSERT", action.arguments["table_name"], action.arguments["primary_key"], action.arguments["row_data"][action.arguments["primary_key"]], preimage_id)

        # 5. Construct final Action object, update DAG & persistence store
        final_action = Action(
            action_id=action.action_id,
            session_id=session_id,
            step_index=current_step,
            tool_name=action.tool_name,
            arguments=action.arguments,
            reasoning=action.reasoning,
            status=ActionStatus.COMMITTED if action_res.success else ActionStatus.FAILED,
            risk_assessment=action.risk_assessment,
            reversibility_class=action.reversibility_class,
            dependencies=action.dependencies,
            inverse_ref=inv_ref,
            checkpoint_id=chk.checkpoint_id,
        )

        self.dag_manager.add_action(final_action)
        await self.repo.save_action(final_action)

        # 6. Stream completion telemetry via EventBus
        await self.event_bus.publish(
            event_type=EventType.ACTION_COMMITTED if action_res.success else EventType.ACTION_FAILED,
            session_id=session_id,
            action_id=final_action.action_id,
            payload={"output": action_res.output, "error": action_res.error_message},
        )

        return StepExecutionResult(
            step_index=current_step,
            proposal=proposal,
            accepted=True,
            action=final_action,
            result=action_res,
        )
