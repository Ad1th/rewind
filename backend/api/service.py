"""Control Plane & Runtime Engine Integration Service."""

import asyncio
from typing import Dict, Optional

from backend.api.websocket import ws_manager
from backend.db.repositories import PersistenceRepository, RollbackRecordEntity
from agent.execution.filesystem import FilesystemSandboxDriver
from agent.execution.git_worktree import GitWorktreeDriver
from agent.rollback.dag import RollbackDAGManager
from agent.rollback.executor import RollbackExecutor, RollbackExecutorSummary
from agent.runtime.checkpoint import CheckpointManager
from agent.runtime.event_bus import RuntimeEvent, RuntimeEventBus


class ControlPlaneRuntimeCoordinator:
    """Wires Runtime, EventBus, Persistence, WebSockets, and Rollback Engine."""

    def __init__(self, repo: Optional[PersistenceRepository] = None) -> None:
        self.repo = repo or PersistenceRepository()
        self.event_bus = RuntimeEventBus()
        self.checkpoint_manager = CheckpointManager()
        self.dag_manager = RollbackDAGManager()
        self.fs_driver = FilesystemSandboxDriver()
        self.git_driver = GitWorktreeDriver()

        self.rollback_executor = RollbackExecutor(
            dag_manager=self.dag_manager,
            checkpoint_manager=self.checkpoint_manager,
            event_bus=self.event_bus,
            fs_driver=self.fs_driver,
            git_driver=self.git_driver,
        )

        # Wire EventBus subscriber to Persistence & WebSocket Gateway
        self.event_bus.subscribe_all(self._on_runtime_event)

    async def _on_runtime_event(self, event: RuntimeEvent) -> None:
        """Handle incoming event from RuntimeEventBus."""
        # 1. Save to relational persistence store
        await self.repo.save_event(event)

        # 2. Broadcast live to WebSocket clients
        await ws_manager.broadcast_event(event.session_id, event)

    async def execute_rollback_from_api(
        self,
        session_id: str,
        target_step_index: int,
        workspace_root: str,
    ) -> RollbackRecordEntity:
        """Execute deterministic rollback triggered via REST API request."""
        summary: RollbackExecutorSummary = await self.rollback_executor.execute_rollback_to_step(
            session_id=session_id,
            target_step_index=target_step_index,
            workspace_root=workspace_root,
        )

        rb_entity = RollbackRecordEntity(
            rollback_plan_id=summary.rollback_plan_id,
            session_id=session_id,
            target_step_index=target_step_index,
            status=summary.status,
            reverted_action_ids=summary.reverted_action_ids,
            failed_action_id=summary.failed_action_id,
            error_message=summary.error_message,
        )

        return await self.repo.save_rollback(rb_entity)
