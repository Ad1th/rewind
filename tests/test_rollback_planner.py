import pytest

from agent.rollback.dag import RollbackDAGManager
from agent.rollback.planner import RollbackPlanner, RollbackStrategy
from agent.runtime.checkpoint import CheckpointManager
from agent.runtime.contracts import Action, InverseOperationReference, RiskAssessment
from agent.tools.models import ReversibilityClass, RiskLevel


@pytest.mark.asyncio
async def test_rollback_planner_builds_ordered_plan(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    dag = RollbackDAGManager()
    chk_mgr = CheckpointManager()

    # Create checkpoint for step 1
    chk1 = await chk_mgr.create_checkpoint("sess-1", "ws-1", 1, str(workspace))

    act1 = Action(
        action_id="act-1",
        session_id="sess-1",
        step_index=1,
        tool_name="fs.create_file",
        arguments={"path": "file1.txt"},
        risk_assessment=RiskAssessment(score=RiskLevel.LOW, rationale="low", requires_approval=False),
        reversibility_class=ReversibilityClass.FULLY_REVERSIBLE,
        inverse_ref=InverseOperationReference(
            inverse_tool_name="fs.delete_file",
            arguments={"path": "file1.txt"},
        ),
    )
    act2 = Action(
        action_id="act-2",
        session_id="sess-1",
        step_index=2,
        tool_name="fs.write_file",
        arguments={"path": "file1.txt"},
        risk_assessment=RiskAssessment(score=RiskLevel.MEDIUM, rationale="med", requires_approval=False),
        reversibility_class=ReversibilityClass.FULLY_REVERSIBLE,
        dependencies=["act-1"],
        inverse_ref=InverseOperationReference(
            inverse_tool_name="fs.restore_preimage",
            arguments={"path": "file1.txt", "preimage_hash": "hash123"},
        ),
    )

    dag.add_action(act1)
    dag.add_action(act2)

    planner = RollbackPlanner(dag, chk_mgr)
    plan = planner.build_plan_for_step("sess-1", 1)

    assert plan.session_id == "sess-1"
    assert plan.target_step_index == 1
    assert plan.target_checkpoint_id == chk1.checkpoint_id
    assert plan.affected_action_ids == ["act-2", "act-1"]
    assert len(plan.execution_steps) == 2

    # Step 1 in plan must be act-2 inverse, Step 2 in plan must be act-1 inverse
    assert plan.execution_steps[0].action_id == "act-2"
    assert plan.execution_steps[0].strategy == RollbackStrategy.INVERSE_OPERATION
    assert plan.execution_steps[1].action_id == "act-1"
    assert plan.execution_steps[1].strategy == RollbackStrategy.INVERSE_OPERATION
