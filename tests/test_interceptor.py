import pytest

from agent.runtime.contracts import ActionProposal, ActionStatus
from agent.runtime.interceptor import ActionInterceptor
from agent.security.policy import PolicyEngine
from agent.security.risk import RiskEngine
from agent.tools.models import ReversibilityClass, RiskLevel, ToolDefinition
from agent.tools.registry import ToolRegistry


@pytest.fixture
def workspace_dir(tmp_path) -> str:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return str(workspace)


@pytest.fixture
def interceptor() -> ActionInterceptor:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="fs.write_file",
            description="Write text to a file",
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
    registry.register(
        ToolDefinition(
            name="fs.delete_file",
            description="Delete a file",
            input_schema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
            permissions=["workspace.write"],
            risk_class=RiskLevel.HIGH,
            reversibility_class=ReversibilityClass.FULLY_REVERSIBLE,
            requires_approval=True,
        )
    )
    registry.register(
        ToolDefinition(
            name="http.post",
            description="Execute external HTTP POST",
            input_schema={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
            permissions=["net.http"],
            risk_class=RiskLevel.CRITICAL,
            reversibility_class=ReversibilityClass.IRREVERSIBLE,
            requires_approval=True,
        )
    )

    policy_engine = PolicyEngine(registry)
    risk_engine = RiskEngine()
    return ActionInterceptor(registry, policy_engine, risk_engine)


def test_valid_proposal_accepted(interceptor: ActionInterceptor, workspace_dir: str):
    proposal = ActionProposal(
        session_id="sess-123",
        tool_name="fs.write_file",
        arguments={"path": "src/main.py", "content": "print('hello')"},
        reasoning="Creating main entry point",
    )

    result = interceptor.intercept_proposal(
        proposal=proposal,
        step_index=1,
        workspace_root=workspace_dir,
        active_permissions=["workspace.write"],
    )

    assert result.accepted is True
    assert result.action is not None
    assert result.action.tool_name == "fs.write_file"
    assert result.action.status == ActionStatus.ASSESSED
    assert result.requires_approval is False


def test_unknown_tool_proposal_rejected(interceptor: ActionInterceptor, workspace_dir: str):
    proposal = ActionProposal(
        session_id="sess-123",
        tool_name="unknown.tool",
        arguments={},
    )

    result = interceptor.intercept_proposal(
        proposal=proposal,
        step_index=1,
        workspace_root=workspace_dir,
    )

    assert result.accepted is False
    assert result.action is None
    assert "Tool 'unknown.tool' is not registered" in result.rejection_reason


def test_invalid_argument_proposal_rejected(interceptor: ActionInterceptor, workspace_dir: str):
    proposal = ActionProposal(
        session_id="sess-123",
        tool_name="fs.write_file",
        arguments={"path": "src/main.py"},  # Missing required 'content'
    )

    result = interceptor.intercept_proposal(
        proposal=proposal,
        step_index=1,
        workspace_root=workspace_dir,
        active_permissions=["workspace.write"],
    )

    assert result.accepted is False
    assert "failed schema validation" in result.rejection_reason


def test_path_traversal_proposal_rejected(interceptor: ActionInterceptor, workspace_dir: str):
    proposal = ActionProposal(
        session_id="sess-123",
        tool_name="fs.write_file",
        arguments={"path": "../../etc/shadow", "content": "hacked"},
    )

    result = interceptor.intercept_proposal(
        proposal=proposal,
        step_index=1,
        workspace_root=workspace_dir,
        active_permissions=["workspace.write"],
    )

    assert result.accepted is False
    assert "PATH_JAIL_VIOLATION" in result.policy_decision.policy_violations[0]


def test_high_risk_proposal_requires_approval(interceptor: ActionInterceptor, workspace_dir: str):
    proposal = ActionProposal(
        session_id="sess-123",
        tool_name="fs.delete_file",
        arguments={"path": "src/old.py"},
    )

    result = interceptor.intercept_proposal(
        proposal=proposal,
        step_index=2,
        workspace_root=workspace_dir,
        active_permissions=["workspace.write"],
    )

    assert result.accepted is True
    assert result.requires_approval is True
    assert result.requires_checkpoint is True
    assert result.action.status == ActionStatus.WAITING_FOR_APPROVAL


def test_irreversible_proposal_requires_approval(interceptor: ActionInterceptor, workspace_dir: str):
    proposal = ActionProposal(
        session_id="sess-123",
        tool_name="http.post",
        arguments={"url": "https://api.stripe.com/charge"},
    )

    result = interceptor.intercept_proposal(
        proposal=proposal,
        step_index=3,
        workspace_root=workspace_dir,
        active_permissions=["net.http"],
    )

    assert result.accepted is True
    assert result.requires_approval is True
    assert result.action.risk_assessment.score == RiskLevel.CRITICAL
    assert result.action.reversibility_class == ReversibilityClass.IRREVERSIBLE


def test_permission_denied_proposal_rejected(interceptor: ActionInterceptor, workspace_dir: str):
    proposal = ActionProposal(
        session_id="sess-123",
        tool_name="fs.write_file",
        arguments={"path": "src/main.py", "content": "print('hello')"},
    )

    result = interceptor.intercept_proposal(
        proposal=proposal,
        step_index=1,
        workspace_root=workspace_dir,
        active_permissions=[],  # Missing workspace.write permission
    )

    assert result.accepted is False
    assert "INSUFFICIENT_PERMISSIONS" in result.policy_decision.policy_violations[0]
