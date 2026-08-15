"""Runtime-Owned Tool Registry Implementation."""

from typing import Any, Dict, List, Optional
from jsonschema import Draft202012Validator, ValidationError

from agent.tools.models import ToolDefinition


class ToolRegistryError(Exception):
    """Base exception for tool registry errors."""
    pass


class DuplicateToolError(ToolRegistryError):
    """Raised when registering a tool that already exists."""
    pass


class UnknownToolError(ToolRegistryError):
    """Raised when querying a tool name that is not registered."""
    pass


class InvalidToolSchemaError(ToolRegistryError):
    """Raised when a tool input schema is structurally invalid."""
    pass


class ToolArgumentValidationError(ToolRegistryError):
    """Raised when tool execution arguments fail JSON schema validation."""
    pass


class ToolRegistry:
    """Authoritative, runtime-owned registry for agent tools.
    
    The LLM cannot modify or inject tool metadata. The runtime registry
    is the single source of truth for schemas, risk levels, permissions, and handlers.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        """Register a new tool definition in the runtime registry.
        
        Raises:
            DuplicateToolError: If a tool with the same name is already registered.
            InvalidToolSchemaError: If input_schema is invalid JSON schema.
        """
        if tool.name in self._tools:
            raise DuplicateToolError(f"Tool '{tool.name}' is already registered in the registry.")
            
        try:
            Draft202012Validator.check_schema(tool.input_schema)
        except Exception as err:
            raise InvalidToolSchemaError(f"Invalid JSON schema for tool '{tool.name}': {err}") from err

        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition:
        """Retrieve a tool definition by name.
        
        Raises:
            UnknownToolError: If no tool is registered under the given name.
        """
        if name not in self._tools:
            raise UnknownToolError(f"Tool '{name}' is not registered in the runtime Tool Registry.")
        return self._tools[name]

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def list_tools(self) -> List[ToolDefinition]:
        """Return all registered tool definitions."""
        return list(self._tools.values())

    def validate_arguments(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input arguments against the registered tool's input schema.
        
        Raises:
            UnknownToolError: If tool is not registered.
            ToolArgumentValidationError: If arguments fail JSON schema validation.
        """
        tool = self.get(name)
        validator = Draft202012Validator(tool.input_schema)
        try:
            validator.validate(arguments)
        except ValidationError as err:
            raise ToolArgumentValidationError(
                f"Arguments for tool '{name}' failed schema validation: {err.message} at path '/' + '/'.join(map(str, err.path))"
            ) from err
        return arguments

    def clear(self) -> None:
        """Clear all registered tools (mainly for testing)."""
        self._tools.clear()
