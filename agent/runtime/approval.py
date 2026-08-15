"""Human-in-the-Loop Runtime Approval Flow Manager."""

from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict

from backend.db.repositories import PersistenceRepository
from agent.runtime.contracts import Action, ActionStatus
from agent.runtime.event_bus import EventType, RuntimeEventBus


class ApprovalDecision(BaseModel):
    action_id: str
    approved: bool
    approver: str = "human_operator"
    reason: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class ApprovalManager:
    """Manages human-in-the-loop approval requests and state transitions for risky tools."""

    def __init__(self, repo: PersistenceRepository, event_bus: RuntimeEventBus) -> None:
        self.repo = repo
        self.event_bus = event_bus

    async def approve_action(self, action_id: str, approver: str = "human_operator") -> Action:
        """Approve a pending high-risk action for execution."""
        action = await self.repo.get_action(action_id)
        if not action:
            raise ValueError(f"Action '{action_id}' not found.")

        updated_action = Action(
            action_id=action.action_id,
            session_id=action.session_id,
            step_index=action.step_index,
            tool_name=action.tool_name,
            arguments=action.arguments,
            reasoning=action.reasoning,
            status=ActionStatus.APPROVED,
            risk_assessment=action.risk_assessment,
            reversibility_class=action.reversibility_class,
            dependencies=action.dependencies,
            inverse_ref=action.inverse_ref,
            checkpoint_id=action.checkpoint_id,
        )

        await self.repo.save_action(updated_action)
        await self.event_bus.publish(
            event_type=EventType.ACTION_VALIDATED,
            session_id=action.session_id,
            action_id=action.action_id,
            payload={"approved_by": approver},
        )
        return updated_action

    async def reject_action(self, action_id: str, reason: str = "User denied permission") -> Action:
        """Reject a pending high-risk action and cancel execution."""
        action = await self.repo.get_action(action_id)
        if not action:
            raise ValueError(f"Action '{action_id}' not found.")

        updated_action = Action(
            action_id=action.action_id,
            session_id=action.session_id,
            step_index=action.step_index,
            tool_name=action.tool_name,
            arguments=action.arguments,
            reasoning=action.reasoning,
            status=ActionStatus.REJECTED,
            risk_assessment=action.risk_assessment,
            reversibility_class=action.reversibility_class,
            dependencies=action.dependencies,
            inverse_ref=action.inverse_ref,
            checkpoint_id=action.checkpoint_id,
        )

        await self.repo.save_action(updated_action)
        await self.event_bus.publish(
            event_type=EventType.ACTION_FAILED,
            session_id=action.session_id,
            action_id=action.action_id,
            payload={"rejection_reason": reason},
        )
        return updated_action
