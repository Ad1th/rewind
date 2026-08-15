import os
import pytest

from backend.api.service import ControlPlaneRuntimeCoordinator
from backend.db.repositories import PersistenceRepository
from agent.execution.filesystem import FilesystemSandboxDriver
from agent.execution.postgres import PostgresRollbackDriver
from agent.llm.provider import DeterministicDemoLLMProvider
from agent.rollback.dag import RollbackDAGManager
from agent.rollback.executor import RollbackExecutor
from agent.rollback.recovery import RollbackFailureRecovery
from agent.rollback.verifier import RollbackVerifier
from agent.runtime.agent_loop import AgentLoop
from agent.runtime.approval import ApprovalManager
from agent.runtime.checkpoint import CheckpointManager
from agent.runtime.contracts import ActionProposal, ActionStatus
from agent.runtime.event_bus import EventType, RuntimeEventBus
from agent.security.policy import PolicyEngine
from agent.security.risk import RiskEngine
from agent.tools.models import ReversibilityClass, RiskLevel, ToolDefinition
from agent.tools.registry import ToolRegistry


@pytest.mark.asyncio
async def test_full_system_e2e_integration(tmp_path):
    workspace_dir = tmp_path / "e2e_full_workspace"
    workspace_dir.mkdir()
    ws_root = str(workspace_dir)

    # 1. Component Wiring
    registry = ToolRegistry()
    registry.register(
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
    registry.register(
        ToolDefinition(
            name="db.insert",
            description="Insert DB row",
            input_schema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string"},
                    "primary_key": {"type": "string"},
                    "row_data": {"type": "object"},
                },
                "required": ["table_name", "primary_key", "row_data"],
            },
            permissions=["db.write"],
            risk_class=RiskLevel.LOW,
            reversibility_class=ReversibilityClass.FULLY_REVERSIBLE,
        )
    )

    policy_engine = PolicyEngine(registry)
    risk_engine = RiskEngine()
    chk_mgr = CheckpointManager()
    dag_mgr = RollbackDAGManager()
    event_bus = RuntimeEventBus()
    repo = PersistenceRepository()
    fs_driver = FilesystemSandboxDriver()
    db_driver = PostgresRollbackDriver()

    # 2. Workspace and Session Creation
    ws = await repo.create_workspace(ws_root, "E2E Workspace")
    session = await repo.create_session(ws_root, "Complete E2E Goal")
    session_id = session.session_id

    # 3. Agent Execution Loop with Multi-Domain Mutations
    proposals = [
        ActionProposal(
            session_id=session_id,
            tool_name="fs.create_file",
            arguments={"path": "app.py", "content": "print('e2e app')"},
            reasoning="Step 1: File creation",
        ),
        ActionProposal(
            session_id=session_id,
            tool_name="db.insert",
            arguments={
                "table_name": "events",
                "primary_key": "id",
                "row_data": {"id": "evt-1", "name": "e2e_event"},
            },
            reasoning="Step 2: Database row insertion",
        ),
    ]

    provider = DeterministicDemoLLMProvider(proposals)
    loop = AgentLoop(
        registry=registry,
        policy_engine=policy_engine,
        risk_engine=risk_engine,
        checkpoint_manager=chk_mgr,
        dag_manager=dag_mgr,
        event_bus=event_bus,
        llm_provider=provider,
        repo=repo,
        fs_driver=fs_driver,
        db_driver=db_driver,
    )

    step1_res = await loop.execute_step(session_id, session.goal_prompt, ws_root)
    assert step1_res.accepted is True
    assert os.path.exists(os.path.join(ws_root, "app.py"))

    step2_res = await loop.execute_step(session_id, session.goal_prompt, ws_root)
    assert step2_res.accepted is True
    assert "events" in db_driver._tables
    assert "evt-1" in db_driver._tables["events"]

    # 4. Rollback Execution to Step 1
    executor = RollbackExecutor(
        dag_manager=dag_mgr,
        checkpoint_manager=chk_mgr,
        event_bus=event_bus,
        fs_driver=fs_driver,
        db_driver=db_driver,
    )

    rb_summary = await executor.execute_rollback_to_step(
        session_id=session_id,
        target_step_index=1,
        workspace_root=ws_root,
    )

    assert rb_summary.status == "RESTORED"

    # 5. Assert DB row step 2 reverted, while app.py step 1 preserved
    assert os.path.exists(os.path.join(ws_root, "app.py"))
    assert "evt-1" not in db_driver._tables.get("events", {})

    # 6. Idempotency Check
    rb_summary2 = await executor.execute_rollback_to_step(
        session_id=session_id,
        target_step_index=1,
        workspace_root=ws_root,
        current_fs_hash=chk_mgr.list_checkpoints(session_id)[0].filesystem_state_ref,
    )
    assert rb_summary2.status in ("SKIPPED_ALREADY_AT_TARGET", "RESTORED")

    # 7. Verify Persistence & Telemetry Stream
    persisted_actions = await repo.list_actions(session_id)
    assert len(persisted_actions) == 2

    events = event_bus.get_events(session_id)
    assert len(events) >= 5
