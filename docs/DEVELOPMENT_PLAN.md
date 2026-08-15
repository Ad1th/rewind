# Development Plan & Roadmap — REWIND

> **Document Version**: 1.0.0 — Implementation Roadmap & Execution Plan  
> **Status**: Complete / Approved  
> **Event**: CUTC: Transform Hackathon 2026  
> **Target Deadline**: August 15, 2026 at 9:30 PM IST  
> **Repository Target**: `~/Documents/Dev/Projects/rewind`  

---

## 1. Hackathon Critical Path & Target Timeline

The primary objective of this development plan is to deliver a fully functional, end-to-end hackathon demonstration of **REWIND** prior to the deadline on **August 15, 2026 at 9:30 PM IST**.

```
[ Phase 0: Repo & Specs ] ──► [ Phase 1: Core Backend & DB ] ──► [ Phase 2: Agent Interceptor ]
       (COMPLETE)                     (Aug 15 Morning)                   (Aug 15 Afternoon)
                                                                                  │
[ Submission & Demo ]   ◄── [ Phase 4: Time Machine UI ]    ◄── [ Phase 3: Rollback Engine ]
  (Aug 15 9:30 PM IST)            (Aug 15 Evening)                   (Aug 15 Late Afternoon)
```

---

## 2. Workstream Architecture & Deliverable Map

```
                               ┌──────────────────────────────────────────────┐
                               │           REWIND WORKSTREAMS                 │
                               └──────────────────────┬───────────────────────┘
                                                      │
         ┌───────────────────┬────────────────────────┼────────────────────────┬───────────────────┐
         ▼                   ▼                        ▼                        ▼                   ▼
┌──────────────────┐┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐┌──────────────────┐
│  WORKSTREAM A    ││   WORKSTREAM B   │    │   WORKSTREAM C   │    │   WORKSTREAM D   ││   WORKSTREAM E   │
│ Backend Plane    ││  Agent Runtime   │    │  Rollback Engine │    │ Persistence (DB) ││ Time Machine UI  │
│ FastAPI Server   ││ Tool Interceptor │    │ Topological DAG  │    │ PostgreSQL Schema││ Next.js 14+ UI   │
│ WebSocket Gateway││ Risk Assessor    │    │ Git Worktree Driver│  │ Alembic Migrations││ Monaco Diff      │
└──────────────────┘└──────────────────┘    └──────────────────┘    └──────────────────┘└──────────────────┘
```

---

## 3. Strict 11-Step Implementation Sequence

To avoid uncoordinated development, implementation will follow an explicit 11-step sequential order:

| Step | Component / Phase | Deliverable | Primary Folder | Target Completion |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Framework Bootstrap** | Initialize FastAPI server (`pyproject.toml`) and Next.js app (`package.json`). | `/backend`, `/frontend` | Aug 15, 14:00 IST |
| **2** | **Database Schema Setup** | Apply PostgreSQL DDL (`sessions`, `action_logs`, `checkpoints`, `inverse_operations`). | `/backend/db` | Aug 15, 14:30 IST |
| **3** | **LLM Provider & Interceptor** | Implement `LLMProvider` wrapper and 16-stage `ActionInterceptor` pipeline. | `/agent` | Aug 15, 15:30 IST |
| **4** | **Tool Registry** | Register `fs` tools (`write`, `create`, `delete`), `git` tools, and `db` tools. | `/agent/tools` | Aug 15, 16:30 IST |
| **5** | **Checkpoint Manager** | Implement Git Worktree snapshot driver and pre-image file copy engine. | `/backend/services` | Aug 15, 17:30 IST |
| **6** | **Rollback Engine** | Implement reverse topological DAG solver and inverse SQL restoration routines. | `/agent/rollback` | Aug 15, 18:30 IST |
| **7** | **WebSocket Telemetry Stream** | Expose `WS /api/v1/sessions/{id}/stream` for live telemetry JSON event broadcasting. | `/backend/api` | Aug 15, 19:00 IST |
| **8** | **Time Machine UI Controls** | Build Next.js 14+ Timeline Scrubber, Action Inspector, and Monaco Diff Viewer. | `/frontend/components` | Aug 15, 20:00 IST |
| **9** | **End-to-End Integration** | Wire Next.js UI to FastAPI WebSocket server; verify live step execution and rollback. | `/` | Aug 15, 20:30 IST |
| **10**| **Integration Testing** | Run automated end-to-end scenario test (`tests/test_e2e_rollback.py`). | `/tests` | Aug 15, 21:00 IST |
| **11**| **Demo Polish & Pitch** | Seed fallback mock data, verify 3-min script, freeze codebase, submit repo. | `/docs/DEMO.md` | Aug 15, 21:30 IST |

---

## 4. Risk-Based Feature Prioritization Matrix

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ P0 (MUST HAVE FOR DEMO)                                                                │
│ • Filesystem tool interception (`write_file`, `create_file`, `delete_file`).           │
│ • Git Worktree zero-copy snapshotting & `git reset` restoration.                       │
│ • PostgreSQL savepoint & pre-image inverse SQL rollback.                               │
│ • Deterministic invariant verification (`tsc` / syntax compiler check).                │
│ • Next.js 14+ visual timeline scrubber with Monaco split-pane diff viewer.             │
│ • Bi-directional WebSocket telemetry streaming (`WS /stream`).                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ P1 (IMPORTANT POLISH)                                                                  │
│ • Risk score badges (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) with visual color tokens.    │
│ • Human approval modal for high-risk tool calls.                                       │
│ • Local LLM response mock fallback mode for zero-latency live judging.                │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ P2 (NICE TO HAVE - POST-HACKATHON)                                                     │
│ • Full Docker container sandboxing for untrusted shell code execution.                 │
│ • Multi-agent parallel DAG execution branching.                                        │
│ • External third-party API webhook rollback handlers.                                  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Explicit Kill List (Features to Abandon under Time Constraint)

If remaining implementation time drops below 2 hours before the deadline:

1. **KILL: Full Docker Container Isolation** $\rightarrow$ Fallback entirely to Git Worktree and jailed path canonicalization.
2. **KILL: Multi-User OAuth Authentication** $\rightarrow$ Fallback to single local developer session context.
3. **KILL: Complex Multi-Agent Swarms** $\rightarrow$ Restrict strictly to single sequential agent workflow.
4. **KILL: Universal External API Inverse Generators** $\rightarrow$ Tag all external HTTP POSTs as `IRREVERSIBLE` with audit warning log.

---

## 6. Definition of Done (DoD) per Milestone

A milestone is considered **DONE** only when:
1. The specified component code passes unit tests without error.
2. Relational state modifications are persisted in PostgreSQL.
3. Relevant telemetry events are broadcast via WebSockets.
4. Clean Git commit is executed with a descriptive subsystem message.
