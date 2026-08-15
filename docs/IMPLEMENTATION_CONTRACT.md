# Implementation Contract — REWIND

> **Document Version**: 1.0.0 — Specification-to-Code Mapping  
> **Status**: Complete / Approved  
> **Event**: CUTC: Transform Hackathon 2026  
> **Repository Target**: `~/Documents/Dev/Projects/rewind`  

---

## 1. Specification-to-Module Mapping Matrix

This document establishes the binding implementation contract between REWIND technical specifications and source code modules.

| Specification Document | Source Module Location | Subsystem Owner | Test Suite Location | Core Dependencies |
| :--- | :--- | :--- | :--- | :--- |
| [`AGENT_WORKFLOW.md`](./AGENT_WORKFLOW.md) | `agent/runtime/` | Agent Interceptor & Runtime | `tests/test_interceptor.py` | `pydantic`, `openai`, `fastapi` |
| [`ROLLBACK_ENGINE.md`](./ROLLBACK_ENGINE.md) | `agent/rollback/` | Rollback Engine | `tests/test_rollback.py` | `gitpython`, `asyncpg` |
| [`EXECUTION_MODEL.md`](./EXECUTION_MODEL.md) | `agent/execution/` | Execution Sandbox Wrapper | `tests/test_sandbox.py` | `gitpython`, `pathlib` |
| [`DATA_MODEL.md`](./DATA_MODEL.md) | `backend/models/` | Domain Entities | `tests/test_models.py` | `sqlalchemy`, `pydantic` |
| [`DATABASE.md`](./DATABASE.md) | `backend/db/` | PostgreSQL Persistence | `tests/test_db.py` | `asyncpg`, `alembic` |
| [`API.md`](./API.md) | `backend/api/` | REST & WebSocket Gateway | `tests/test_api.py` | `fastapi`, `websockets` |
| [`SECURITY.md`](./SECURITY.md) | `agent/security/` | Security Policy & Path Jailing | `tests/test_security.py` | `re`, `pathlib` |
| [`UX.md`](./UX.md) | `frontend/src/` | Time Machine Visual UI | `frontend/tests/` | `next`, `react`, `framer-motion` |

---

## 2. Subsystem Responsibilities & Entry Points

### 2.1 Backend Control Plane (`backend/`)
- **Entry Point**: `backend/main.py`
- **Modules**:
  * `backend/api/router.py`: Exposes REST endpoints (`/api/v1/sessions`).
  * `backend/api/websocket.py`: Bi-directional WebSocket event gateway (`/stream`).
  * `backend/db/session.py`: Async PostgreSQL database connection pool (`asyncpg`).
  * `backend/models/domain.py`: SQLAlchemy & Pydantic domain data models.

### 2.2 Agent Runtime & Sandbox (`agent/`)
- **Entry Point**: `agent/runtime/engine.py`
- **Modules**:
  * `agent/runtime/interceptor.py`: 16-stage tool call interception pipeline.
  * `agent/runtime/registry.py`: REWIND Tool Registry with schema & risk metadata.
  * `agent/execution/sandbox.py`: Jailed path validator & Git Worktree driver.
  * `agent/rollback/engine.py`: Reverse topological DAG solver & inverse SQL driver.
  * `agent/security/policy.py`: Regex secret filter & permission enforcement.

### 2.3 Time Machine UI (`frontend/`)
- **Entry Point**: `frontend/src/app/page.tsx`
- **Components**:
  * `frontend/src/components/TimelineScrubber.tsx`: Live step scrubber track.
  * `frontend/src/components/ActionInspector.tsx`: Step metadata & evidence viewer.
  * `frontend/src/components/DiffViewer.tsx`: Monaco visual split-pane diff viewer.
  * `frontend/src/components/RollbackModal.tsx`: Single-click `Ctrl+Z` confirmation modal.
