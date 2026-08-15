"""Action Interceptor Pipeline Implementation."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from agent.runtime.contracts import Action, ActionProposal, ActionStatus, RiskAssessment
from agent.security.policy import PolicyEngine, PolicyEvaluationResult
from agent.security.risk import RiskEngine
from agent.tools.models import ReversibilityClass, RiskLevel, ToolDefinition
from agent.tools.registry import ToolArgumentValidationError, ToolRegistry, UnknownToolError


class InterceptionResult(BaseModel):
    """Structured result produced by the Action Interceptor pipeline."""

    accepted: bool
    action: Optional[Action] = None
    policy_decision: PolicyEvaluationResult
    risk_assessment: Optional[RiskAssessment] = None
    requires_approval: bool = False
    requires_checkpoint: bool = False
    rejection_reason: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class ActionInterceptor:
    """16-Stage Deterministic Interception Pipeline between LLM and Sandbox execution.
    
    Validates, parses, evaluates security policies, assesses risk, determines reversibility
    and checkpoint requirements before handing off for sandbox execution.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        policy_engine: PolicyEngine,
        risk_engine: RiskEngine,
    ) -> None:
        self.registry = registry
        self.policy_engine = policy_engine
        self.risk_engine = risk_engine

    def intercept_proposal(
        self,
        proposal: ActionProposal,
        step_index: int,
        workspace_root: str,
        active_permissions: Optional[List[str]] = None,
        parent_action_ids: Optional[List[str]] = None,
    ) -> InterceptionResult:
        """Run proposal through the 16-stage interception pipeline.
        
        Args:
            proposal: Untrusted LLM ActionProposal.
            step_index: 1-indexed execution step integer.
            workspace_root: Managed workspace root path.
            active_permissions: List of granted permission scopes.
            parent_action_ids: Optional dependency parent action IDs.
            
        Returns:
            InterceptionResult detailing acceptance status, policy decisions, risk assessment,
            and the runtime-approved Action object if accepted.
        """
        # Stage 1 & 2: Tool Registry Lookup
        try:
            tool: ToolDefinition = self.registry.get(proposal.tool_name)
        except UnknownToolError as err:
            policy_fail = PolicyEvaluationResult(
                allowed=False,
                reason=str(err),
                policy_violations=[f"UNKNOWN_TOOL: {proposal.tool_name}"],
            )
            return InterceptionResult(
                accepted=False,
                policy_decision=policy_fail,
                rejection_reason=f"Tool '{proposal.tool_name}' is not registered.",
            )

        # Stage 3: Argument Schema Validation
        try:
            self.registry.validate_arguments(proposal.tool_name, proposal.arguments)
        except ToolArgumentValidationError as err:
            policy_fail = PolicyEvaluationResult(
                allowed=False,
                reason=str(err),
                policy_violations=[f"SCHEMA_VALIDATION_FAILURE: {err}"],
            )
            return InterceptionResult(
                accepted=False,
                policy_decision=policy_fail,
                rejection_reason=f"Arguments for '{proposal.tool_name}' failed schema validation.",
            )

        # Stage 4 & 5: Security & Policy Evaluation
        policy_decision = self.policy_engine.evaluate_proposal(
            tool_name=proposal.tool_name,
            arguments=proposal.arguments,
            workspace_root=workspace_root,
            active_permissions=active_permissions,
        )
        if not policy_decision.allowed:
            return InterceptionResult(
                accepted=False,
                policy_decision=policy_decision,
                rejection_reason=f"Security policy evaluation failed: {policy_decision.reason}",
            )

        # Stage 6 & 7: Risk Engine Evaluation
        risk_assessment = self.risk_engine.evaluate(
            tool=tool,
            arguments=proposal.arguments,
        )

        # Stage 8: Reversibility & Checkpoint Decision
        requires_checkpoint = (
            risk_assessment.score in (RiskLevel.HIGH, RiskLevel.CRITICAL)
            or tool.reversibility_class in (ReversibilityClass.STATE_RESTORABLE, ReversibilityClass.PARTIALLY_REVERSIBLE)
        )

        # Stage 9: Approval Gate Decision
        requires_approval = risk_assessment.requires_approval

        # Stage 10: Action Status Initialization
        initial_status = (
            ActionStatus.WAITING_FOR_APPROVAL
            if requires_approval
            else ActionStatus.ASSESSED
        )

        # Stage 11: Construct Runtime-Approved Action Node
        action = Action(
            session_id=proposal.session_id,
            step_index=step_index,
            tool_name=proposal.tool_name,
            arguments=proposal.arguments,
            reasoning=proposal.reasoning,
            expected_effect=f"Execute {proposal.tool_name} with risk {risk_assessment.score.value}",
            risk_assessment=risk_assessment,
            reversibility_class=tool.reversibility_class,
            dependencies=parent_action_ids or [],
            status=initial_status,
        )

        return InterceptionResult(
            accepted=True,
            action=action,
            policy_decision=policy_decision,
            risk_assessment=risk_assessment,
            requires_approval=requires_approval,
            requires_checkpoint=requires_checkpoint,
        )
