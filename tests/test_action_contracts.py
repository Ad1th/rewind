import pytest
from agent.runtime.contracts import (
    Action,
    ActionProposal,
    ActionResult,
    ActionStatus,
    InverseOperationReference,
    RiskAssessment,
    VerificationResult,
)
from agent.tools.models import ReversibilityClass, RiskLevel


def test_action_proposal_creation():
    proposal = ActionProposal(
        session_id="sess-123",
        tool_name="fs.write_file",
        arguments={"path": "src/app.py", "content": "print('hello')"},
        reasoning="Adding entry point",
    )
    assert proposal.session_id == "sess-123"
    assert proposal.tool_name == "fs.write_file"
    assert proposal.proposal_id is not None


def test_action_contract_lifecycle():
    risk = RiskAssessment(
        score=RiskLevel.MEDIUM,
        rationale="File edit operation",
        requires_approval=False,
        factors=["file_edit"],
    )
    action = Action(
        session_id="sess-123",
        step_index=1,
        tool_name="fs.write_file",
        arguments={"path": "src/app.py", "content": "print('hello')"},
        reasoning="Adding entry point",
        risk_assessment=risk,
        reversibility_class=ReversibilityClass.FULLY_REVERSIBLE,
    )

    assert action.status == ActionStatus.PROPOSED
    assert action.risk_assessment.score == RiskLevel.MEDIUM
    assert action.reversibility_class == ReversibilityClass.FULLY_REVERSIBLE

    # Update status to COMMITTED
    action.status = ActionStatus.COMMITTED
    action.verification_ref = VerificationResult(passed=True, output="Syntax check OK")
    action.inverse_ref = InverseOperationReference(
        inverse_tool_name="fs.restore_preimage",
        arguments={"path": "src/app.py", "preimage_hash": "abc123hash"},
    )

    assert action.status == ActionStatus.COMMITTED
    assert action.verification_ref.passed is True
    assert action.inverse_ref.inverse_tool_name == "fs.restore_preimage"


def test_action_result_creation():
    result = ActionResult(success=True, output={"bytes_written": 42}, execution_time_ms=12.5)
    assert result.success is True
    assert result.output["bytes_written"] == 42
