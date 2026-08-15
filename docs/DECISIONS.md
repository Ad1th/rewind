# Architecture Decision Records (ADRs) — REWIND

> **Status**: Active Log  
> **Event**: CUTC: Transform Hackathon 2026  
> **Repository Target**: `~/Documents/Dev/Projects/rewind`  

---

## ADR-001: Initial Repository & Documentation Structure
- **Date**: 2026-08-11
- **Status**: Accepted
- **Context**: Setting up repository foundation for CUTC Transform Hackathon 2026.
- **Decision**: Establish modular initial directory structure separating `docs/`, `backend/`, `frontend/`, `agent/`, `infra/`, and `tests/`. All detailed technical designs will be documented in `docs/` before implementation begins.
- **Consequences**: Ensures clean separation of concerns and technical clarity prior to coding.

---

## ADR-002: Real-time Communication via Bi-directional WebSockets
- **Date**: 2026-08-15
- **Status**: Accepted
- **Context**: The frontend Time Machine UI requires real-time telemetry streaming from the backend control plane during agent execution, as well as the ability to send immediate control signals (pause, step, rewind).
- **Decision**: Adopt WebSockets (`WS /api/v1/sessions/{session_id}/stream`) as the primary communication protocol for live action events and interactive control plane operations. Server-Sent Events (SSE) was considered but lacks native bi-directional message capabilities.
- **Consequences**: Provides low-latency (<50ms) event delivery for live visual UI scrubbing and immediate pause/rollback commands.

---

## ADR-003: State Isolation via Git Worktrees and DB Transaction Savepoints
- **Date**: 2026-08-15
- **Status**: Accepted
- **Context**: State snapshotting must be lightweight, fast, and 100% deterministic for local codebases and database targets without requiring heavy virtual machine images for every single tool call.
- **Decision**: Use Git Worktrees and automated commit snapshotting for filesystem operations, coupled with PostgreSQL `SAVEPOINT` / explicit transaction blocks for database mutations. Docker containers will serve as optional sandboxes for untrusted shell execution.
- **Consequences**: Zero-copy/instant snapshot performance for filesystem diffs; complete isolation of agent side-effects with minimal disk overhead.

---

## ADR-004: Deterministic Hybrid Rollback Engine Architecture
- **Date**: 2026-08-15
- **Status**: Accepted
- **Context**: Rollback cannot rely on generative LLM prompts to "undo" mistakes due to hallucination risks. Rollback engine must handle complex multi-step dependency graphs.
- **Decision**: Combine pre-action state snapshots (Git commits, DB savepoints, file diffs) with topological execution of inverse action recipes along the Action Dependency DAG.
- **Consequences**: Guarantees deterministic, 100% accurate environment restoration without invoking the LLM during state rewind.
