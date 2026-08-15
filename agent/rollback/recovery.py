"""Rollback Failure Recovery and Partial Restoration Handler."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from agent.rollback.executor import RollbackExecutorSummary
from agent.runtime.checkpoint import CheckpointManager, CheckpointRecord


class RecoveryAuditReport(BaseModel):
    """Audit report detailing emergency containment during a failed or partial rollback."""

    session_id: str
    target_step_index: int
    emergency_checkpoint_id: str
    status: str
    reverted_action_ids: List[str]
    failed_action_id: Optional[str]
    audit_summary: str

    model_config = ConfigDict(frozen=True)


class RollbackFailureRecovery:
    """Handles partial rollback containment and emergency snapshot creation."""

    def __init__(self, checkpoint_manager: CheckpointManager) -> None:
        self.checkpoint_manager = checkpoint_manager

    async def handle_partial_failure(
        self,
        session_id: str,
        workspace_root: str,
        summary: RollbackExecutorSummary,
    ) -> RecoveryAuditReport:
        """Create an emergency checkpoint and produce an audit recovery report for partial rollbacks."""
        # 1. Create emergency checkpoint to lock current partial state
        emergency_chk: CheckpointRecord = await self.checkpoint_manager.create_checkpoint(
            session_id=session_id,
            workspace_id="emergency_containment",
            step_index=summary.target_step_index,
            workspace_root=workspace_root,
            metadata={
                "recovery_event": "EMERGENCY_PARTIAL_ROLLBACK_CONTAINMENT",
                "failed_action_id": summary.failed_action_id,
            },
        )

        audit = (
            f"EMERGENCY_PARTIAL_ROLLBACK_CONTAINMENT: Rollback to step {summary.target_step_index} resulted in status '{summary.status}'. "
            f"Reverted actions: {len(summary.reverted_action_ids)}. "
            f"Failed on action: '{summary.failed_action_id}'. "
            f"Emergency checkpoint captured at '{emergency_chk.checkpoint_id}'."
        )

        return RecoveryAuditReport(
            session_id=session_id,
            target_step_index=summary.target_step_index,
            emergency_checkpoint_id=emergency_chk.checkpoint_id,
            status=summary.status,
            reverted_action_ids=summary.reverted_action_ids,
            failed_action_id=summary.failed_action_id,
            audit_summary=audit,
        )
