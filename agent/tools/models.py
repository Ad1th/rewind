"""Tool Registry Models and Data Structures."""

from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ReversibilityClass(str, Enum):
    FULLY_REVERSIBLE = "FULLY_REVERSIBLE"
    STATE_RESTORABLE = "STATE_RESTORABLE"
    PARTIALLY_REVERSIBLE = "PARTIALLY_REVERSIBLE"
    IRREVERSIBLE = "IRREVERSIBLE"


class ToolDefinition(BaseModel):
    """Authoritative, runtime-owned definition of an agent tool."""
    
    name: str = Field(..., description="Canonical tool name, e.g. 'fs.write_file'")
    version: str = Field(default="1.0.0", description="SemVer string of the tool specification")
    description: str = Field(..., description="Description of the tool purpose")
    input_schema: Dict[str, Any] = Field(..., description="JSON Schema for input argument validation")
    output_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for tool output")
    permissions: List[str] = Field(default_factory=list, description="Required permission scopes")
    risk_class: RiskLevel = Field(..., description="Runtime risk classification")
    reversibility_class: ReversibilityClass = Field(..., description="Runtime reversibility classification")
    execution_handler: Optional[Callable[..., Any]] = Field(default=None, exclude=True)
    verification_handler: Optional[Callable[..., Any]] = Field(default=None, exclude=True)
    inverse_strategy: Optional[Callable[..., Any]] = Field(default=None, exclude=True)
    supported_environment: List[str] = Field(default_factory=lambda: ["local", "worktree", "docker"])
    requires_approval: bool = Field(default=False, description="Whether human confirmation is required")

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
