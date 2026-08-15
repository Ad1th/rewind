"""Runtime-Owned Risk Engine Implementation."""

from typing import Any, Dict, List, Optional
from agent.runtime.contracts import RiskAssessment
from agent.tools.models import ReversibilityClass, RiskLevel, ToolDefinition


class RiskEngine:
    """Evaluates risk levels and approval requirements deterministically."""

    def evaluate(
        self,
        tool: ToolDefinition,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> RiskAssessment:
        """Calculate runtime risk score based on tool metadata and argument inspection.
        
        The LLM's opinion or reasoning cannot override deterministic risk policies.
        """
        factors: List[str] = []
        score = tool.risk_class
        requires_approval = tool.requires_approval

        # Check for irreversibility
        if tool.reversibility_class == ReversibilityClass.IRREVERSIBLE:
            score = RiskLevel.CRITICAL
            requires_approval = True
            factors.append("irreversible_external_effect")

        # Check for deletion / destructive file tools
        tool_name_lower = tool.name.lower()
        if "delete" in tool_name_lower or "drop" in tool_name_lower or "rm" in tool_name_lower:
            if score != RiskLevel.CRITICAL:
                score = RiskLevel.HIGH
            requires_approval = True
            factors.append("destructive_operation")

        # Check for raw shell / terminal execution
        if "shell" in tool_name_lower or "terminal" in tool_name_lower or "exec" in tool_name_lower:
            score = RiskLevel.CRITICAL
            requires_approval = True
            factors.append("raw_code_execution")

        # Check batch size / path factors
        if "path" in arguments and isinstance(arguments["path"], str):
            path_str = arguments["path"]
            if path_str.endswith(".env") or "secret" in path_str.lower() or "config" in path_str.lower():
                if score == RiskLevel.LOW:
                    score = RiskLevel.MEDIUM
                factors.append("sensitive_configuration_file")

        rationale = f"Assessed as {score.value} risk. Factors: {', '.join(factors) if factors else 'Standard policy'}."

        return RiskAssessment(
            score=score,
            rationale=rationale,
            requires_approval=requires_approval,
            factors=factors,
        )
