import pytest

from backend.db.repositories import PersistenceRepository
from agent.runtime.approval import ApprovalManager
from agent.runtime.contracts import Action, ActionStatus, RiskAssessment
from agent.runtime.event_bus import EventType, RuntimeEventBus
from agent.tools.models import ReversibilityClass, RiskLevel


@pytest.mark.asyncio
async def test_approval_flow():
    repo = PersistenceRepository()
    event_bus = RuntimeEventBus()
    approval_mgr = ApprovalManager(repo, event_bus)

    act = Action(
        action_id="act-high-risk",
        session_id="sess-risk",
        step_index=1,
        tool_name="fs.delete_file",
        arguments={"path": "important.py"},
        status=ActionStatus.WAITING_FOR_APPROVAL,
        risk_assessment=RiskAssessment(score=RiskLevel.HIGH, rationale="high", requires_approval=True),
        reversibility_class=ReversibilityClass.FULLY_REVERSIBLE,
    )
    await repo.save_action(act)

    # Approve action
    approved = await approval_mgr.approve_action("act-high-risk")
    assert approved.status == ActionStatus.APPROVED

    events = event_bus.get_events("sess-risk")
    assert events[-1].event_type == EventType.ACTION_VALIDATED

    # Reject action
    rejected = await approval_mgr.reject_action("act-high-risk", reason="Dangerous operation")
    assert rejected.status == ActionStatus.REJECTED
