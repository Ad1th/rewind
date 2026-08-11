# API Specification — REWIND

> **Status**: Draft / Pending Detailed Specification  

---

## 1. Overview

The REWIND API exposes endpoints for:
- Initializing and configuring agent sessions.
- Streaming real-time agent execution events and state updates.
- Manually creating or inspecting checkpoints.
- Triggering single-step or multi-step rollbacks.
- Querying action trees, state diffs, and risk analysis metrics.

---

## 2. Endpoint Categories

- `POST /api/v1/sessions`: Start new agent session.
- `GET /api/v1/sessions/{session_id}/timeline`: Retrieve full action timeline and dependency graph.
- `POST /api/v1/sessions/{session_id}/checkpoints`: Manual snapshot capture.
- `POST /api/v1/sessions/{session_id}/rollback`: Execute rollback to specified checkpoint or action ID.
- `WS /api/v1/sessions/{session_id}/stream`: Real-time WebSocket connection for live agent activity & state changes.
