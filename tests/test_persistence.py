import pytest
from backend.db.repositories import (
    PersistenceRepository,
    RollbackRecordEntity,
    SessionEntity,
    WorkspaceEntity,
)
from agent.runtime.contracts import Action, RiskAssessment
from agent.tools.models import ReversibilityClass, RiskLevel


@pytest.fixture
def repo() -> PersistenceRepository:
    return PersistenceRepository()


@pytest.mark.asyncio
async def test_workspace_and_session_persistence(repo: PersistenceRepository):
    ws = await repo.create_workspace("/tmp/workspace", "Test Workspace")
    assert ws.workspace_id is not None
    assert ws.workspace_root == "/tmp/workspace"

    fetched_ws = await repo.get_workspace(ws.workspace_id)
    assert fetched_ws == ws

    session = await repo.create_session("/tmp/workspace", "Clean workspace")
    assert session.session_id is not None
    assert session.status == "SESSION_CREATED"

    updated = await repo.update_session_status(session.session_id, "RUNNING")
    assert updated.status == "RUNNING"

    fetched_sess = await repo.get_session(session.session_id)
    assert fetched_sess.status == "RUNNING"


@pytest.mark.asyncio
async def test_action_and_rollback_persistence(repo: PersistenceRepository):
    act = Action(
        action_id="act-101",
        session_id="sess-55",
        step_index=1,
        tool_name="fs.write_file",
        arguments={"path": "main.py"},
        risk_assessment=RiskAssessment(score=RiskLevel.LOW, rationale="low", requires_approval=False),
        reversibility_class=ReversibilityClass.FULLY_REVERSIBLE,
    )
    saved_act = await repo.save_action(act)
    assert saved_act.action_id == "act-101"

    actions = await repo.list_actions("sess-55")
    assert len(actions) == 1
    assert actions[0].action_id == "act-101"

    rb = RollbackRecordEntity(
        rollback_plan_id="plan-1",
        session_id="sess-55",
        target_step_index=1,
        status="RESTORED",
        reverted_action_ids=["act-101"],
    )
    saved_rb = await repo.save_rollback(rb)
    assert saved_rb.rollback_id is not None

    rollbacks = await repo.list_rollbacks("sess-55")
    assert len(rollbacks) == 1
    assert rollbacks[0].status == "RESTORED"
