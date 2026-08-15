"""Canonical REWIND Hackathon Demo Orchestration."""

import os
from typing import Dict, Any
from pydantic import BaseModel, ConfigDict

from backend.db.repositories import PersistenceRepository
from agent.execution.filesystem import FilesystemSandboxDriver
from agent.execution.git_worktree import GitWorktreeDriver
from agent.llm.provider import DeterministicDemoLLMProvider
from agent.rollback.dag import RollbackDAGManager
from agent.rollback.executor import RollbackExecutor, RollbackExecutorSummary
from agent.runtime.agent_loop import AgentLoop
from agent.runtime.checkpoint import CheckpointManager
from agent.runtime.contracts import ActionProposal
from agent.runtime.event_bus import RuntimeEventBus
from agent.security.policy import PolicyEngine
from agent.security.risk import RiskEngine
from agent.tools.models import ReversibilityClass, RiskLevel, ToolDefinition
from agent.tools.registry import ToolRegistry


class DemoExecutionSummary(BaseModel):
    session_id: str
    workspace_root: str
    total_steps_executed: int
    rollback_summary: RollbackExecutorSummary

    model_config = ConfigDict(frozen=True)


class CanonicalDemoRunner:
    """Runs the 14-stage canonical hackathon demonstration scenario through the real REWIND runtime."""

    def __init__(self, workspace_root: str) -> None:
        self.workspace_root = workspace_root
        os.makedirs(workspace_root, exist_ok=True)

        self.registry = ToolRegistry()
        self._register_tools()

        self.policy_engine = PolicyEngine(self.registry)
        self.risk_engine = RiskEngine()
        self.checkpoint_manager = CheckpointManager()
        self.dag_manager = RollbackDAGManager()
        self.event_bus = RuntimeEventBus()
        self.repo = PersistenceRepository()
        self.fs_driver = FilesystemSandboxDriver()
        self.git_driver = GitWorktreeDriver()

        self.executor = RollbackExecutor(
            dag_manager=self.dag_manager,
            checkpoint_manager=self.checkpoint_manager,
            event_bus=self.event_bus,
            fs_driver=self.fs_driver,
            git_driver=self.git_driver,
        )

    def _register_tools(self) -> None:
        self.registry.register(
            ToolDefinition(
                name="fs.create_file",
                description="Create file",
                input_schema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                    "required": ["path", "content"],
                },
                permissions=["workspace.write"],
                risk_class=RiskLevel.LOW,
                reversibility_class=ReversibilityClass.FULLY_REVERSIBLE,
            )
        )
        self.registry.register(
            ToolDefinition(
                name="fs.write_file",
                description="Write file",
                input_schema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                    "required": ["path", "content"],
                },
                permissions=["workspace.write"],
                risk_class=RiskLevel.MEDIUM,
                reversibility_class=ReversibilityClass.FULLY_REVERSIBLE,
            )
        )
        self.registry.register(
            ToolDefinition(
                name="fs.delete_file",
                description="Delete file",
                input_schema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
                permissions=["workspace.write"],
                risk_class=RiskLevel.HIGH,
                reversibility_class=ReversibilityClass.FULLY_REVERSIBLE,
                requires_approval=False,
            )
        )

    async def run_canonical_demo(self, session_id: str = "sess-canonical-demo") -> DemoExecutionSummary:
        """Run the full 14-stage canonical hackathon demo."""
        # Choreographed proposals passed through un-mocked interceptor & sandbox drivers
        demo_proposals = [
            ActionProposal(
                session_id=session_id,
                tool_name="fs.create_file",
                arguments={"path": "src/main.py", "content": "print('v1 initial app')"},
                reasoning="Step 1: Initializing application entry point",
            ),
            ActionProposal(
                session_id=session_id,
                tool_name="fs.write_file",
                arguments={"path": "src/main.py", "content": "print('v2 feature added')"},
                reasoning="Step 2: Adding main logic feature",
            ),
            ActionProposal(
                session_id=session_id,
                tool_name="fs.create_file",
                arguments={"path": "config.json", "content": '{"env": "production"}'},
                reasoning="Step 3: Creating config file",
            ),
            ActionProposal(
                session_id=session_id,
                tool_name="fs.delete_file",
                arguments={"path": "src/main.py"},
                reasoning="Step 4: Flawed accidental deletion of main entry point",
            ),
        ]

        demo_provider = DeterministicDemoLLMProvider(demo_proposals)
        loop = AgentLoop(
            registry=self.registry,
            policy_engine=self.policy_engine,
            risk_engine=self.risk_engine,
            checkpoint_manager=self.checkpoint_manager,
            dag_manager=self.dag_manager,
            event_bus=self.event_bus,
            llm_provider=demo_provider,
            repo=self.repo,
            fs_driver=self.fs_driver,
            git_driver=self.git_driver,
        )

        # Execute 4 steps
        for _ in range(4):
            await loop.execute_step(
                session_id=session_id,
                goal_prompt="Canonical Demo Task",
                workspace_root=self.workspace_root,
            )

        # Trigger REWIND to Step 2
        summary = await self.executor.execute_rollback_to_step(
            session_id=session_id,
            target_step_index=2,
            workspace_root=self.workspace_root,
        )

        return DemoExecutionSummary(
            session_id=session_id,
            workspace_root=self.workspace_root,
            total_steps_executed=4,
            rollback_summary=summary,
        )
