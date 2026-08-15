"""Deterministic Rollback Planner Implementation."""

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field

from agent.rollback.dag import RollbackDAGManager
from agent.runtime.checkpoint import CheckpointManager, CheckpointRecord
from agent.runtime.contracts import Action, InverseOperationReference


class RollbackStrategy(str, Enum):
    INVERSE_OPERATION = "INVERSE_OPERATION"
    GIT_WORKTREE_CHECKOUT = "GIT_WORKTREE_CHECKOUT"
    FILESYSTEM_PREIMAGE_RESTORE = "FILESYSTEM_PREIMAGE_RESTORE"


class RollbackStepItem(BaseModel):
    """Single step element in a Rollback Execution Plan."""

    sequence_index: int
    action_id: str
    tool_name: str
    strategy: RollbackStrategy
    target_resource: str
    inverse_recipe: Optional[InverseOperationReference] = None
    git_commit_hash: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class RollbackPlan(BaseModel):
    """Immutable Rollback Execution Plan produced by the Rollback Planner."""

    rollback_plan_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    target_step_index: int
    target_checkpoint_id: Optional[str] = None
    affected_action_ids: List[str]
    execution_steps: List[RollbackStepItem]
    expected_final_hash: str
    requires_verification: bool = True

    model_config = ConfigDict(frozen=True)


class RollbackPlannerError(Exception):
    """Base exception for Rollback Planner operations."""
    pass


class RollbackPlanner:
    """Constructs deterministic rollback execution plans using DAG topology and Checkpoint metadata."""

    def __init__(self, dag_manager: RollbackDAGManager, checkpoint_manager: CheckpointManager) -> None:
        self.dag_manager = dag_manager
        self.checkpoint_manager = checkpoint_manager

    def build_plan_for_step(self, session_id: str, target_step_index: int) -> RollbackPlan:
        """Construct a RollbackPlan to restore workspace to target_step_index."""
        target_action = self.dag_manager.get_action_by_step(target_step_index)
        
        # 1. Compute reverse topological rollback sequence
        ordered_actions: List[Action] = self.dag_manager.compute_reverse_topological_order(target_action.action_id)
        
        # 2. Query target checkpoint
        checkpoints = self.checkpoint_manager.list_checkpoints(session_id)
        target_chk: Optional[CheckpointRecord] = None
        for chk in checkpoints:
            if chk.step_index == target_step_index:
                target_chk = chk
                break

        expected_hash = target_chk.integrity_hash if target_chk else "unverified_target_hash"

        # 3. Construct RollbackStepItems in reverse topological order
        execution_steps: List[RollbackStepItem] = []
        for idx, act in enumerate(ordered_actions, start=1):
            if act.inverse_ref is not None:
                strategy = RollbackStrategy.INVERSE_OPERATION
                inverse_recipe = act.inverse_ref
                git_hash = None
            elif target_chk and target_chk.git_state_ref:
                strategy = RollbackStrategy.GIT_WORKTREE_CHECKOUT
                inverse_recipe = None
                git_hash = target_chk.git_state_ref
            else:
                strategy = RollbackStrategy.FILESYSTEM_PREIMAGE_RESTORE
                inverse_recipe = None
                git_hash = None

            step_item = RollbackStepItem(
                sequence_index=idx,
                action_id=act.action_id,
                tool_name=act.tool_name,
                strategy=strategy,
                target_resource=str(act.arguments.get("path", act.arguments.get("target_path", "workspace"))),
                inverse_recipe=inverse_recipe,
                git_commit_hash=git_hash,
            )
            execution_steps.append(step_item)

        return RollbackPlan(
            session_id=session_id,
            target_step_index=target_step_index,
            target_checkpoint_id=target_chk.checkpoint_id if target_chk else None,
            affected_action_ids=[act.action_id for act in ordered_actions],
            execution_steps=execution_steps,
            expected_final_hash=expected_hash,
            requires_verification=True,
        )
