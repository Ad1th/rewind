# REST & WebSocket API Specification — REWIND

> **Document Version**: 1.0.0 — API Gateway Specification  
> **Status**: Complete / Approved  
> **Protocol**: REST (HTTP/2) + WebSockets (Bi-directional)  
> **Repository Target**: `~/Documents/Dev/Projects/rewind`  

---

## 1. REST Endpoints Summary

### Session Management
- `POST /api/v1/sessions` — Start new agent session.
  * Body: `{ "goal_prompt": string, "workspace_root": string }`
  * Response: `201 Created` with `AgentSession` entity.
- `GET /api/v1/sessions/{session_id}` — Get active session state.
- `POST /api/v1/sessions/{session_id}/pause` — Pause execution.
- `POST /api/v1/sessions/{session_id}/resume` — Resume execution.

### Rollback Control
- `POST /api/v1/sessions/{session_id}/rollback` — Execute rollback to step or checkpoint.
  * Body: `{ "target_step_index": number, "target_checkpoint_id"?: string }`
  * Response: `200 OK` with `RollbackSummary`.

### Action & Timeline Queries
- `GET /api/v1/sessions/{session_id}/timeline` — Get action DAG & chronological timeline.
- `GET /api/v1/sessions/{session_id}/diffs/{action_id}` — Get Monaco split-pane diff payload.

---

## 2. WebSocket Telemetry Gateway (`WS /api/v1/sessions/{session_id}/stream`)

### Bi-directional Message Contract

#### Client-to-Server Messages
* `PAUSE_SESSION`: Instantly pause agent execution.
* `RESUME_SESSION`: Resume execution.
* `APPROVE_ACTION`: Approve pending `HIGH`/`CRITICAL` risk step.
* `DENY_ACTION`: Deny pending step.

#### Server-to-Client Events
* `ACTION_PROPOSED`: `{"event_type": "ACTION_PROPOSED", "payload": ActionPayload}`
* `RISK_ASSESSED`: `{"event_type": "RISK_ASSESSED", "payload": RiskPayload}`
* `CHECKPOINT_CREATED`: `{"event_type": "CHECKPOINT_CREATED", "payload": CheckpointPayload}`
* `ACTION_COMMITTED`: `{"event_type": "ACTION_COMMITTED", "payload": ActionNodePayload}`
* `ROLLBACK_STARTED`: `{"event_type": "ROLLBACK_STARTED", "payload": RollbackPayload}`
* `ROLLBACK_COMPLETED`: `{"event_type": "ROLLBACK_COMPLETED", "payload": RollbackResultPayload}`
