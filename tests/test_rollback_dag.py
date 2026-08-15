import pytest

from agent.rollback.dag import DAGCycleError, RollbackDAGManager
from agent.runtime.contracts import Action, RiskAssessment
from agent.tools.models import ReversibilityClass, RiskLevel


@pytest.fixture
def dag_manager() -> RollbackDAGManager:
    return RollbackDAGManager()


def make_action(action_id: str, step_index: int, dependencies=None) -> Action:
    return Action(
        action_id=action_id,
        session_id="sess-1",
        step_index=step_index,
        tool_name="fs.write_file",
        arguments={"path": f"file_{step_index}.txt"},
        risk_assessment=RiskAssessment(score=RiskLevel.LOW, rationale="low risk", requires_approval=False),
        reversibility_class=ReversibilityClass.FULLY_REVERSIBLE,
        dependencies=dependencies or [],
    )


def test_dag_addition_and_reverse_topological_sort(dag_manager: RollbackDAGManager):
    act1 = make_action("act-1", 1)
    act2 = make_action("act-2", 2, dependencies=["act-1"])
    act3 = make_action("act-3", 3, dependencies=["act-2"])

    dag_manager.add_action(act1)
    dag_manager.add_action(act2)
    dag_manager.add_action(act3)

    descendants = dag_manager.get_descendants("act-1")
    assert descendants == {"act-2", "act-3"}

    reverse_order = dag_manager.compute_reverse_topological_order("act-1")
    order_ids = [a.action_id for a in reverse_order]

    # Must execute act-3 first, then act-2, then act-1
    assert order_ids == ["act-3", "act-2", "act-1"]


def test_dag_branching_reverse_order(dag_manager: RollbackDAGManager):
    # Act 1 -> Act 2 and Act 3 -> Act 4 (merges Act 2 & Act 3)
    act1 = make_action("act-1", 1)
    act2 = make_action("act-2", 2, dependencies=["act-1"])
    act3 = make_action("act-3", 3, dependencies=["act-1"])
    act4 = make_action("act-4", 4, dependencies=["act-2", "act-3"])

    dag_manager.add_action(act1)
    dag_manager.add_action(act2)
    dag_manager.add_action(act3)
    dag_manager.add_action(act4)

    reverse_order = dag_manager.compute_reverse_topological_order("act-1")
    order_ids = [a.action_id for a in reverse_order]

    # act-4 must be first (depends on 2 & 3), then 2 and 3, then 1
    assert order_ids[0] == "act-4"
    assert order_ids[-1] == "act-1"
    assert set(order_ids[1:3]) == {"act-2", "act-3"}


def test_dag_cycle_detection(dag_manager: RollbackDAGManager):
    act1 = make_action("act-1", 1, dependencies=["act-2"])
    act2 = make_action("act-2", 2, dependencies=["act-1"])

    dag_manager.add_action(act1)
    with pytest.raises(DAGCycleError):
        dag_manager.add_action(act2)
