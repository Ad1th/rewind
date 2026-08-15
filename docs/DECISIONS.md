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

---

## ADR-005: Runtime-Enforced Tool Metadata & Untrusted LLM Planner Model
- **Date**: 2026-08-15
- **Status**: Accepted
- **Context**: The LLM may hallucinate tool arguments, permissions, or risk levels, or attempt unauthorized authority escalation.
- **Decision**: All tool metadata, risk classifications, schema validations, sandboxing rules, and inverse generation strategies belong strictly to the REWIND Runtime Tool Registry. The LLM is treated strictly as an untrusted proposal engine.
- **Consequences**: Complete runtime defense against prompt injection, hallucinated tool calls, and unauthorized privilege escalation.

---

## ADR-006: Post-Commit PostgreSQL Historical Rollback via Row Pre-Image Inverse Recipes
- **Date**: 2026-08-15
- **Status**: Accepted
- **Context**: PostgreSQL `SAVEPOINT`s only function within active uncommitted transactions. Once a tool action commits to the database, savepoints are invalidated.
- **Decision**: For uncommitted transaction steps, use native PostgreSQL `SAVEPOINT`s. For post-commit historical rollbacks, execute row-level pre-image inverse SQL operations (`DELETE` inserted rows, `UPDATE` columns back to pre-image values).
- **Consequences**: Honest, deterministic PostgreSQL state restoration without requiring perpetual open database transactions across multi-step agent sessions.

---

## ADR-007: Event Stream Immutability & Merkle Root Checkpoint Chaining
- **Date**: 2026-08-15
- **Status**: Accepted
- **Context**: Historical action logs and checkpoints must be tamper-resistant to guarantee provenance auditing.
- **Decision**: Every checkpoint computes a SHA-256 Merkle root hash linking the Git worktree commit hash, filesystem tree hash, and PostgreSQL pre-image delta. Database action logs are strictly append-only.
- **Consequences**: Immutable audit trail; instant integrity validation during rollback verification.

---

## ADR-008: Strict API Idempotency via Workspace State Hashing
- **Date**: 2026-08-15
- **Status**: Accepted
- **Context**: Double-submitting a rollback request could trigger duplicate execution loops.
- **Decision**: All REST rollback endpoints (`POST /api/v1/sessions/{id}/rollback`) compare the current workspace Merkle hash against the target checkpoint hash before executing. If identical, the request immediately returns `SKIPPED_ALREADY_AT_TARGET`.
- **Consequences**: Safe, idempotent API operations under network retries or accidental double-clicks.
