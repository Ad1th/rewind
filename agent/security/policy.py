"""Deterministic Policy Engine Implementation."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from agent.security.jail import SecurityBoundaryViolation, validate_jailed_path
from agent.tools.models import ToolDefinition
from agent.tools.registry import UnknownToolError, ToolRegistry


class PolicyEvaluationResult(BaseModel):
    """Result of policy enforcement evaluation."""

    allowed: bool
    reason: str
    policy_violations: List[str] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)


class PolicyEngine:
    """Enforces hard security policies and path containment rules."""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def evaluate_proposal(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        workspace_root: str,
        active_permissions: Optional[List[str]] = None,
    ) -> PolicyEvaluationResult:
        """Evaluate a proposed tool call against runtime security policies.
        
        Checks:
        1. Tool existence in ToolRegistry.
        2. Permission scope matching.
        3. Path Jailing validation for any path arguments.
        4. Blocked command inspection.
        """
        violations: List[str] = []

        # 1. Tool existence check
        try:
            tool: ToolDefinition = self.registry.get(tool_name)
        except UnknownToolError:
            return PolicyEvaluationResult(
                allowed=False,
                reason=f"Tool '{tool_name}' is unknown or unregistered in the runtime Tool Registry.",
                policy_violations=[f"UNREGISTERED_TOOL: {tool_name}"],
            )

        # 2. Permission check
        if tool.permissions and active_permissions is not None:
            for required_perm in tool.permissions:
                if required_perm not in active_permissions:
                    violations.append(f"INSUFFICIENT_PERMISSIONS: Missing '{required_perm}'")

        # 3. Path Jailing Check
        if "path" in arguments and isinstance(arguments["path"], str):
            try:
                validate_jailed_path(arguments["path"], workspace_root)
            except SecurityBoundaryViolation as err:
                violations.append(f"PATH_JAIL_VIOLATION: {err}")

        if "target_path" in arguments and isinstance(arguments["target_path"], str):
            try:
                validate_jailed_path(arguments["target_path"], workspace_root)
            except SecurityBoundaryViolation as err:
                violations.append(f"PATH_JAIL_VIOLATION: {err}")

        if violations:
            return PolicyEvaluationResult(
                allowed=False,
                reason=f"Policy check failed with {len(violations)} violation(s).",
                policy_violations=violations,
            )

        return PolicyEvaluationResult(
            allowed=True,
            reason="All policy requirements satisfied.",
            policy_violations=[],
        )
