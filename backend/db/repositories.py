"""PostgreSQL & Relational Data Access Layer Repositories."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field

from agent.runtime.checkpoint import CheckpointRecord
from agent.runtime.contracts import Action, ActionStatus
from agent.runtime.event_bus import EventType, RuntimeEvent


class WorkspaceEntity(BaseModel):
    workspace_id: str = Field(default_factory=lambda: str(uuid4()))
    workspace_root: str
    name: str = Field(default="default_workspace")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = ConfigDict(frozen=True)


class SessionEntity(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    workspace_root: str
    goal_prompt: str
    status: str = Field(default="SESSION_CREATED")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = ConfigDict(frozen=False)


class RollbackRecordEntity(BaseModel):
    rollback_id: str = Field(default_factory=lambda: str(uuid4()))
    rollback_plan_id: str
    session_id: str
    target_step_index: int
    status: str
    reverted_action_ids: List[str] = Field(default_factory=list)
    failed_action_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = ConfigDict(frozen=True)


class PersistenceRepository:
    """Thread-safe relational data repository for REWIND state persistence."""

    def __init__(self) -> None:
        self._workspaces: Dict[str, WorkspaceEntity] = {}
        self._sessions: Dict[str, SessionEntity] = {}
        self._actions: Dict[str, Action] = {}
        self._checkpoints: Dict[str, CheckpointRecord] = {}
        self._rollbacks: Dict[str, RollbackRecordEntity] = {}
        self._events: Dict[str, List[RuntimeEvent]] = {}

    # --- Workspaces ---
    async def create_workspace(self, workspace_root: str, name: str = "default_workspace") -> WorkspaceEntity:
        ws = WorkspaceEntity(workspace_root=workspace_root, name=name)
        self._workspaces[ws.workspace_id] = ws
        return ws

    async def get_workspace(self, workspace_id: str) -> Optional[WorkspaceEntity]:
        return self._workspaces.get(workspace_id)

    # --- Sessions ---
    async def create_session(self, workspace_root: str, goal_prompt: str) -> SessionEntity:
        session = SessionEntity(workspace_root=workspace_root, goal_prompt=goal_prompt)
        self._sessions[session.session_id] = session
        return session

    async def get_session(self, session_id: str) -> Optional[SessionEntity]:
        return self._sessions.get(session_id)

    async def update_session_status(self, session_id: str, status: str) -> Optional[SessionEntity]:
        session = self._sessions.get(session_id)
        if session:
            session.status = status
            session.updated_at = datetime.now(timezone.utc).isoformat()
        return session

    # --- Actions ---
    async def save_action(self, action: Action) -> Action:
        self._actions[action.action_id] = action
        return action

    async def get_action(self, action_id: str) -> Optional[Action]:
        return self._actions.get(action_id)

    async def list_actions(self, session_id: str) -> List[Action]:
        actions = [a for a in self._actions.values() if a.session_id == session_id]
        return sorted(actions, key=lambda a: a.step_index)

    # --- Checkpoints ---
    async def save_checkpoint(self, checkpoint: CheckpointRecord) -> CheckpointRecord:
        self._checkpoints[checkpoint.checkpoint_id] = checkpoint
        return checkpoint

    async def get_checkpoint(self, checkpoint_id: str) -> Optional[CheckpointRecord]:
        return self._checkpoints.get(checkpoint_id)

    async def list_checkpoints(self, session_id: str) -> List[CheckpointRecord]:
        chks = [c for c in self._checkpoints.values() if c.session_id == session_id]
        return sorted(chks, key=lambda c: c.step_index)

    # --- Rollbacks ---
    async def save_rollback(self, rollback: RollbackRecordEntity) -> RollbackRecordEntity:
        self._rollbacks[rollback.rollback_id] = rollback
        return rollback

    async def get_rollback(self, rollback_id: str) -> Optional[RollbackRecordEntity]:
        return self._rollbacks.get(rollback_id)

    async def list_rollbacks(self, session_id: str) -> List[RollbackRecordEntity]:
        rbs = [r for r in self._rollbacks.values() if r.session_id == session_id]
        return sorted(rbs, key=lambda r: r.created_at)

    # --- Events ---
    async def save_event(self, event: RuntimeEvent) -> RuntimeEvent:
        if event.session_id not in self._events:
            self._events[event.session_id] = []
        self._events[event.session_id].append(event)
        return event

    async def list_events(self, session_id: str, after_sequence: int = 0) -> List[RuntimeEvent]:
        events = self._events.get(session_id, [])
        filtered = [e for e in events if e.sequence_number > after_sequence]
        return sorted(filtered, key=lambda e: e.sequence_number)
