"""WebSocket Telemetry Gateway for Live Streaming & Event Replay."""

import asyncio
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.db.repositories import PersistenceRepository
from agent.runtime.event_bus import RuntimeEvent, RuntimeEventBus

ws_router = APIRouter(prefix="/api/v1", tags=["WebSocket Telemetry"])


class ConnectionManager:
    """Manages active WebSocket telemetry streaming connections per session."""

    def __init__(self) -> None:
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def broadcast_event(self, session_id: str, event: RuntimeEvent) -> None:
        """Broadcast a canonical RuntimeEvent to all connected clients for session_id."""
        if session_id not in self.active_connections:
            return

        json_str = event.model_dump_json()
        dead_sockets = set()
        for websocket in self.active_connections[session_id]:
            try:
                await websocket.send_text(json_str)
            except Exception:
                dead_sockets.add(websocket)

        for dead_ws in dead_sockets:
            self.disconnect(session_id, dead_ws)


ws_manager = ConnectionManager()


@ws_router.websocket("/sessions/{session_id}/stream")
async def session_telemetry_stream(
    websocket: WebSocket,
    session_id: str,
    after_sequence: int = 0,
):
    """Live WebSocket telemetry stream with reconnect/replay support."""
    await ws_manager.connect(session_id, websocket)
    try:
        # Replay historical events if after_sequence is specified
        if after_sequence > 0:
            repo = PersistenceRepository()
            past_events = await repo.list_events(session_id, after_sequence=after_sequence)
            for event in past_events:
                await websocket.send_text(event.model_dump_json())

        # Keep connection open for live telemetry streaming
        while True:
            # Client can send ping frames or control messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id, websocket)
    except Exception:
        ws_manager.disconnect(session_id, websocket)
