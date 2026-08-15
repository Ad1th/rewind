import os
import pytest

from agent.security.jail import SecurityBoundaryViolation, validate_jailed_path
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
def registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(
        ToolDefinition(
            name="fs.write_file",
            description="Write content to a file",
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
    reg.register(
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
    reg.register(
        ToolDefinition(
            name="shell.execute",
            description="Execute arbitrary shell command",
            input_schema={
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
            permissions=["system.exec"],
            risk_class=RiskLevel.CRITICAL,
            reversibility_class=ReversibilityClass.IRREVERSIBLE,
            requires_approval=True,
        )
    )
    return reg


# --- Path Jailing Tests ---

def test_valid_jailed_path(workspace_dir: str):
    valid_rel = "src/main.py"
    validated = validate_jailed_path(valid_rel, workspace_dir)
    assert validated.startswith(os.path.realpath(workspace_dir))


def test_relative_path_traversal_blocked(workspace_dir: str):
    traversal_path = "../../etc/passwd"
    with pytest.raises(SecurityBoundaryViolation):
        validate_jailed_path(traversal_path, workspace_dir)


def test_absolute_path_escape_blocked(workspace_dir: str):
    absolute_escape = "/etc/passwd"
    with pytest.raises(SecurityBoundaryViolation):
        validate_jailed_path(absolute_escape, workspace_dir)


def test_forbidden_system_path_blocked(workspace_dir: str):
    forbidden_path = "/usr/local/bin"
    with pytest.raises(SecurityBoundaryViolation):
        validate_jailed_path(forbidden_path, workspace_dir)


# --- Policy Engine Tests ---

def test_policy_engine_valid_proposal(registry: ToolRegistry, workspace_dir: str):
    engine = PolicyEngine(registry)
    result = engine.evaluate_proposal(
        tool_name="fs.write_file",
        arguments={"path": "src/app.py", "content": "print('ok')"},
        workspace_root=workspace_dir,
        active_permissions=["workspace.write"],
    )
    assert result.allowed is True
    assert len(result.policy_violations) == 0


def test_policy_engine_unknown_tool(registry: ToolRegistry, workspace_dir: str):
    engine = PolicyEngine(registry)
    result = engine.evaluate_proposal(
        tool_name="unknown.tool",
        arguments={},
        workspace_root=workspace_dir,
    )
    assert result.allowed is False
    assert "UNREGISTERED_TOOL" in result.policy_violations[0]


def test_policy_engine_path_traversal_denied(registry: ToolRegistry, workspace_dir: str):
    engine = PolicyEngine(registry)
    result = engine.evaluate_proposal(
        tool_name="fs.write_file",
        arguments={"path": "../../../etc/shadow", "content": "malicious"},
        workspace_root=workspace_dir,
        active_permissions=["workspace.write"],
    )
    assert result.allowed is False
    assert "PATH_JAIL_VIOLATION" in result.policy_violations[0]


def test_policy_engine_insufficient_permissions(registry: ToolRegistry, workspace_dir: str):
    engine = PolicyEngine(registry)
    result = engine.evaluate_proposal(
        tool_name="fs.write_file",
        arguments={"path": "src/app.py", "content": "print('ok')"},
        workspace_root=workspace_dir,
        active_permissions=[],  # Missing workspace.write
    )
    assert result.allowed is False
    assert "INSUFFICIENT_PERMISSIONS" in result.policy_violations[0]


# --- Risk Engine Tests ---

def test_risk_engine_evaluation(registry: ToolRegistry):
    risk_engine = RiskEngine()

    # Medium risk tool
    write_tool = registry.get("fs.write_file")
    assessment = risk_engine.evaluate(write_tool, {"path": "src/app.py"})
    assert assessment.score == RiskLevel.MEDIUM
    assert assessment.requires_approval is False

    # High risk destructive tool
    delete_tool = registry.get("fs.delete_file")
    assessment_del = risk_engine.evaluate(delete_tool, {"path": "src/app.py"})
    assert assessment_del.score == RiskLevel.HIGH
    assert assessment_del.requires_approval is True
    assert "destructive_operation" in assessment_del.factors

    # Critical risk shell tool
    shell_tool = registry.get("shell.execute")
    assessment_shell = risk_engine.evaluate(shell_tool, {"command": "rm -rf /"})
    assert assessment_shell.score == RiskLevel.CRITICAL
    assert assessment_shell.requires_approval is True
    assert "raw_code_execution" in assessment_shell.factors
