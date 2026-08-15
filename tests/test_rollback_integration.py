import os
import pytest

from agent.execution.filesystem import FilesystemSandboxDriver
from agent.rollback.dag import RollbackDAGManager
from agent.rollback.executor import RollbackExecutor
from agent.rollback.recovery import RollbackFailureRecovery
from agent.runtime.checkpoint import CheckpointManager
from agent.runtime.contracts import Action, InverseOperationReference, RiskAssessment
from agent.runtime.event_bus import EventType, RuntimeEvent, RuntimeEventBus
from agent.tools.models import ReversibilityClass, RiskLevel


@pytest.fixture
def workspace(tmp_path) -> str:
    ws = tmp_path / "workspace"
    ws.mkdir()
    return str(ws)


@pytest.fixture
def components():
    dag = RollbackDAGManager()
    chk_mgr = CheckpointManager()
    event_bus = RuntimeEventBus()
    fs_driver = FilesystemSandboxDriver()
    executor = RollbackExecutor(
        dag_manager=dag,
        checkpoint_manager=chk_mgr,
        event_bus=event_bus,
        fs_driver=fs_driver,
    )
    recovery = RollbackFailureRecovery(chk_mgr)
    return {
        "dag": dag,
        "chk_mgr": chk_mgr,
        "event_bus": event_bus,
        "fs_driver": fs_driver,
        "executor": executor,
        "recovery": recovery,
    }


@pytest.mark.asyncio
async def test_e2e_multi_step_rollback_integration(components, workspace: str):
    dag: RollbackDAGManager = components["dag"]
    chk_mgr: CheckpointManager = components["chk_mgr"]
    event_bus: RuntimeEventBus = components["event_bus"]
    fs_driver: FilesystemSandboxDriver = components["fs_driver"]
    executor: RollbackExecutor = components["executor"]

    session_id = "sess-e2e-1"
    rel_path1 = "src/app.py"
    rel_path2 = "src/utils.py"

    # --- Step 1: Create src/app.py ---
    pre_hash1, exists1 = fs_driver.capture_preimage(rel_path1, workspace)
    fs_driver.create_file(rel_path1, "print('step 1')", workspace)
    chk1 = await chk_mgr.create_checkpoint(session_id, "ws-1", 1, workspace)
    inv1 = fs_driver.generate_inverse_recipe("fs.create_file", {"path": rel_path1}, pre_hash1, exists1)

    act1 = Action(
        action_id="act-1",
        session_id=session_id,
        step_index=1,
        tool_name="fs.create_file",
        arguments={"path": rel_path1},
        risk_assessment=RiskAssessment(score=RiskLevel.LOW, rationale="low", requires_approval=False),
        reversibility_class=ReversibilityClass.FULLY_REVERSIBLE,
        inverse_ref=inv1,
        checkpoint_id=chk1.checkpoint_id,
    )
    dag.add_action(act1)

    # --- Step 2: Edit src/app.py ---
    pre_hash2, exists2 = fs_driver.capture_preimage(rel_path1, workspace)
    fs_driver.write_file(rel_path1, "print('step 2 modified')", workspace)
    chk2 = await chk_mgr.create_checkpoint(session_id, "ws-1", 2, workspace)
    inv2 = fs_driver.generate_inverse_recipe("fs.write_file", {"path": rel_path1}, pre_hash2, exists2)

    act2 = Action(
        action_id="act-2",
        session_id=session_id,
        step_index=2,
        tool_name="fs.write_file",
        arguments={"path": rel_path1},
        risk_assessment=RiskAssessment(score=RiskLevel.MEDIUM, rationale="med", requires_approval=False),
        reversibility_class=ReversibilityClass.FULLY_REVERSIBLE,
        dependencies=["act-1"],
        inverse_ref=inv2,
        checkpoint_id=chk2.checkpoint_id,
    )
    dag.add_action(act2)

    # --- Step 3: Create src/utils.py (Flawed Step) ---
    pre_hash3, exists3 = fs_driver.capture_preimage(rel_path2, workspace)
    fs_driver.create_file(rel_path2, "import invalid_module", workspace)
    chk3 = await chk_mgr.create_checkpoint(session_id, "ws-1", 3, workspace)
    inv3 = fs_driver.generate_inverse_recipe("fs.create_file", {"path": rel_path2}, pre_hash3, exists3)

    act3 = Action(
        action_id="act-3",
        session_id=session_id,
        step_index=3,
        tool_name="fs.create_file",
        arguments={"path": rel_path2},
        risk_assessment=RiskAssessment(score=RiskLevel.HIGH, rationale="high", requires_approval=True),
        reversibility_class=ReversibilityClass.FULLY_REVERSIBLE,
        dependencies=["act-2"],
        inverse_ref=inv3,
        checkpoint_id=chk3.checkpoint_id,
    )
    dag.add_action(act3)

    # Assert current workspace state before rollback
    assert os.path.exists(os.path.join(workspace, rel_path1))
    assert os.path.exists(os.path.join(workspace, rel_path2))

    # --- Trigger Rollback to Step 1 ---
    summary = await executor.execute_rollback_to_step(
        session_id=session_id,
        target_step_index=1,
        workspace_root=workspace,
    )

    assert summary.status == "RESTORED"
    assert summary.reverted_action_ids == ["act-3", "act-2"]

    # Assert workspace restored state
    assert not os.path.exists(os.path.join(workspace, rel_path2))  # Flawed utils.py deleted
    with open(os.path.join(workspace, rel_path1)) as f:
        assert f.read() == "print('step 1')"  # app.py restored to step 1 content

    # Assert EventBus streamed events
    events = event_bus.get_events(session_id)
    event_types = [e.event_type for e in events]
    assert EventType.ROLLBACK_REQUESTED in event_types
    assert EventType.ROLLBACK_PLANNED in event_types
    assert EventType.ROLLBACK_STARTED in event_types
    assert EventType.ROLLBACK_COMPLETED in event_types


@pytest.mark.asyncio
async def test_rollback_idempotency_adr_008(components, workspace: str):
    dag: RollbackDAGManager = components["dag"]
    chk_mgr: CheckpointManager = components["chk_mgr"]
    fs_driver: FilesystemSandboxDriver = components["fs_driver"]
    executor: RollbackExecutor = components["executor"]

    session_id = "sess-idempotent"
    rel_path = "data.txt"

    pre_hash, exists = fs_driver.capture_preimage(rel_path, workspace)
    fs_driver.create_file(rel_path, "initial", workspace)
    chk1 = await chk_mgr.create_checkpoint(session_id, "ws-1", 1, workspace)
    inv1 = fs_driver.generate_inverse_recipe("fs.create_file", {"path": rel_path}, pre_hash, exists)

    act1 = Action(
        action_id="act-1",
        session_id=session_id,
        step_index=1,
        tool_name="fs.create_file",
        arguments={"path": rel_path},
        risk_assessment=RiskAssessment(score=RiskLevel.LOW, rationale="low", requires_approval=False),
        reversibility_class=ReversibilityClass.FULLY_REVERSIBLE,
        inverse_ref=inv1,
    )
    dag.add_action(act1)

    # 1. Execute Rollback to step 1
    summary1 = await executor.execute_rollback_to_step(
        session_id=session_id,
        target_step_index=1,
        workspace_root=workspace,
    )

    # 2. Execute second identical rollback request
    summary2 = await executor.execute_rollback_to_step(
        session_id=session_id,
        target_step_index=1,
        workspace_root=workspace,
        current_git_hash=chk1.git_state_ref,
        current_fs_hash=chk1.filesystem_state_ref,
    )

    assert summary2.status == "SKIPPED_ALREADY_AT_TARGET"


@pytest.mark.asyncio
async def test_partial_rollback_failure_containment(components, workspace: str):
    dag: RollbackDAGManager = components["dag"]
    chk_mgr: CheckpointManager = components["chk_mgr"]
    executor: RollbackExecutor = components["executor"]
    recovery: RollbackFailureRecovery = components["recovery"]

    session_id = "sess-partial"
    rel_path = "locked_file.txt"

    # Action 1 at step 2 with invalid preimage hash to force error during rollback to step 1
    act1 = Action(
        action_id="act-1",
        session_id=session_id,
        step_index=2,
        tool_name="fs.create_file",
        arguments={"path": rel_path},
        risk_assessment=RiskAssessment(score=RiskLevel.LOW, rationale="low", requires_approval=False),
        reversibility_class=ReversibilityClass.FULLY_REVERSIBLE,
        inverse_ref=InverseOperationReference(
            inverse_tool_name="fs.restore_preimage",
            arguments={"path": rel_path, "preimage_hash": "nonexistent_hash_to_trigger_error"},
        ),
    )
    dag.add_action(act1)

    summary = await executor.execute_rollback_to_step(
        session_id=session_id,
        target_step_index=1,
        workspace_root=workspace,
    )

    assert summary.status in ("FAILED", "PARTIALLY_RESTORED")
    assert summary.failed_action_id == "act-1"

    # Run recovery protocol
    report = await recovery.handle_partial_failure(session_id, workspace, summary)
    assert report.status == summary.status
    assert report.emergency_checkpoint_id is not None
    assert "EMERGENCY_PARTIAL_ROLLBACK_CONTAINMENT" in report.audit_summary
