"""Runtime Event Bus and Event Telemetry Pipeline."""

import asyncio
import logging
from datetime import datetime, timezone
from enum import Enum
from inspect import iscoroutinefunction
from typing import Any, Awaitable, Callable, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("rewind.event_bus")


class EventType(str, Enum):
    SESSION_STARTED = "SESSION_STARTED"
    PLAN_CREATED = "PLAN_CREATED"
    ACTION_PROPOSED = "ACTION_PROPOSED"
    ACTION_VALIDATED = "ACTION_VALIDATED"
    RISK_ASSESSED = "RISK_ASSESSED"
    CHECKPOINT_CREATED = "CHECKPOINT_CREATED"
    ACTION_STARTED = "ACTION_STARTED"
    ACTION_COMPLETED = "ACTION_COMPLETED"
    ACTION_FAILED = "ACTION_FAILED"
    VERIFICATION_STARTED = "VERIFICATION_STARTED"
    VERIFICATION_COMPLETED = "VERIFICATION_COMPLETED"
    ACTION_COMMITTED = "ACTION_COMMITTED"
    ROLLBACK_REQUESTED = "ROLLBACK_REQUESTED"
    ROLLBACK_PLANNED = "ROLLBACK_PLANNED"
    ROLLBACK_STARTED = "ROLLBACK_STARTED"
    ROLLBACK_ACTION_STARTED = "ROLLBACK_ACTION_STARTED"
    ROLLBACK_ACTION_COMPLETED = "ROLLBACK_ACTION_COMPLETED"
    ROLLBACK_ACTION_FAILED = "ROLLBACK_ACTION_FAILED"
    ROLLBACK_PARTIAL = "ROLLBACK_PARTIAL"
    ROLLBACK_VERIFICATION_STARTED = "ROLLBACK_VERIFICATION_STARTED"
    ROLLBACK_VERIFICATION_FAILED = "ROLLBACK_VERIFICATION_FAILED"
    ROLLBACK_COMPLETED = "ROLLBACK_COMPLETED"
    ROLLBACK_FAILED = "ROLLBACK_FAILED"


class RuntimeEvent(BaseModel):
    """Canonical event envelope for internal runtime telemetry and WebSocket broadcasting."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    sequence_number: int
    session_id: str
    action_id: Optional[str] = None
    event_type: EventType
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None

    model_config = ConfigDict(frozen=True)


EventHandler = Callable[[RuntimeEvent], Optional[Awaitable[None]]]


class RuntimeEventBus:
    """Async event bus for internal telemetry publishing and WebSocket subscriber routing."""

    def __init__(self) -> None:
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._global_handlers: List[EventHandler] = []
        self._session_sequences: Dict[str, int] = {}
        self._event_history: Dict[str, List[RuntimeEvent]] = {}

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Register a handler callback for a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        """Register a handler callback for all event types."""
        self._global_handlers.append(handler)

    async def publish(
        self,
        event_type: EventType,
        session_id: str,
        payload: Dict[str, Any],
        action_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> RuntimeEvent:
        """Construct, log, and publish an event to all subscribed handlers.
        
        Assigns a monotonically increasing sequence_number per session_id.
        """
        # Calculate next sequence number for session
        current_seq = self._session_sequences.get(session_id, 0) + 1
        self._session_sequences[session_id] = current_seq

        event = RuntimeEvent(
            sequence_number=current_seq,
            session_id=session_id,
            action_id=action_id,
            event_type=event_type,
            payload=payload,
            correlation_id=correlation_id,
        )

        # Record in event history
        if session_id not in self._event_history:
            self._event_history[session_id] = []
        self._event_history[session_id].append(event)

        # Notify type-specific handlers
        target_handlers = self._handlers.get(event_type, []) + self._global_handlers
        for handler in target_handlers:
            await self._invoke_handler(handler, event)

        return event

    async def _invoke_handler(self, handler: EventHandler, event: RuntimeEvent) -> None:
        """Safely invoke sync or async handler callback."""
        try:
            if iscoroutinefunction(handler):
                await handler(event)
            else:
                res = handler(event)
                if asyncio.iscoroutine(res):
                    await res
        except Exception as err:
            logger.error("Error in event handler %s: %s", handler, err)

    def get_events(self, session_id: str) -> List[RuntimeEvent]:
        """Retrieve ordered history of published events for a session."""
        return list(self._event_history.get(session_id, []))

    def clear(self) -> None:
        """Reset event bus state (for testing)."""
        self._handlers.clear()
        self._global_handlers.clear()
        self._session_sequences.clear()
        self._event_history.clear()
