import pytest
from pydantic import ValidationError

from agent.tools.models import ReversibilityClass, RiskLevel, ToolDefinition
from agent.tools.registry import (
    DuplicateToolError,
    InvalidToolSchemaError,
    ToolArgumentValidationError,
    ToolRegistry,
    UnknownToolError,
)


@pytest.fixture
def registry() -> ToolRegistry:
    return ToolRegistry()


@pytest.fixture
def dummy_tool() -> ToolDefinition:
    return ToolDefinition(
        name="fs.write_file",
        version="1.0.0",
        description="Write text content to a target file path",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
        risk_class=RiskLevel.MEDIUM,
        reversibility_class=ReversibilityClass.FULLY_REVERSIBLE,
        supported_environment=["local", "worktree"],
    )


def test_tool_registration_and_lookup(registry: ToolRegistry, dummy_tool: ToolDefinition):
    registry.register(dummy_tool)
    assert registry.has_tool("fs.write_file")
    
    retrieved = registry.get("fs.write_file")
    assert retrieved.name == "fs.write_file"
    assert retrieved.risk_class == RiskLevel.MEDIUM
    assert retrieved.reversibility_class == ReversibilityClass.FULLY_REVERSIBLE


def test_duplicate_tool_registration_fails(registry: ToolRegistry, dummy_tool: ToolDefinition):
    registry.register(dummy_tool)
    with pytest.raises(DuplicateToolError):
        registry.register(dummy_tool)


def test_unknown_tool_lookup_fails(registry: ToolRegistry):
    with pytest.raises(UnknownToolError):
        registry.get("nonexistent.tool")


def test_invalid_schema_registration_fails(registry: ToolRegistry):
    invalid_tool = ToolDefinition(
        name="invalid.tool",
        description="Tool with invalid schema",
        input_schema={"type": "invalid_type"},  # Invalid JSON Schema type
        risk_class=RiskLevel.LOW,
        reversibility_class=ReversibilityClass.FULLY_REVERSIBLE,
    )
    with pytest.raises(InvalidToolSchemaError):
        registry.register(invalid_tool)


def test_tool_argument_validation(registry: ToolRegistry, dummy_tool: ToolDefinition):
    registry.register(dummy_tool)
    
    # Valid arguments
    valid_args = {"path": "src/main.py", "content": "print('hello')"}
    validated = registry.validate_arguments("fs.write_file", valid_args)
    assert validated == valid_args

    # Invalid arguments (missing required 'content')
    invalid_args = {"path": "src/main.py"}
    with pytest.raises(ToolArgumentValidationError):
        registry.validate_arguments("fs.write_file", invalid_args)


def test_metadata_immutability(dummy_tool: ToolDefinition):
    # Pydantic model_config = ConfigDict(frozen=True) prevents mutation
    with pytest.raises(ValidationError):
        dummy_tool.risk_class = RiskLevel.CRITICAL  # Mutating frozen attribute must fail
