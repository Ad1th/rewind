# System Architecture — REWIND

> **Status**: Draft / Pending Detailed Specification  

---

## 1. High-Level Architecture Overview

REWIND consists of four primary subsystems:

1. **Frontend (Time Machine UI)**: Next.js + React + Framer Motion visual control interface displaying action timelines, visual state diffs, risk badges, and rollback controls.
2. **Backend Control Plane (FastAPI)**: REST & WebSocket server orchestrating agent sessions, managing state checkpoints, risk evaluation, and database persistence.
3. **Agent Runtime & Execution Layer**: Python-based tool execution sandbox with structured tool wrappers, inverse action generators, and step interceptors.
4. **Persistence Layer (PostgreSQL)**: Stores session metadata, action logs, dependency DAGs, checkpoint snapshots, and verification audit logs.

---

## 2. Component Diagram Sketch

```
 [ Next.js Time Machine UI ] <== WebSocket / REST ==> [ FastAPI Control Plane ]
                                                              ||
                                                 +------------+------------+
                                                 |                         |
                                       [ Agent Runtime ]           [ PostgreSQL DB ]
                                       (Tool Interceptors)         (Action Logs & State)
                                                 |
                                       [ Sandboxed Environment ]
                                       (Filesystem / Git / Docker / DB)
```

---

## 3. Subsystem Responsibilities

### Control Plane & API
- Session management & state streaming.
- Checkpoint registry & restore triggers.

### Agent Interceptor & Sandbox
- Intercepts all LLM tool calls before execution.
- Evaluates risk score and generates inverse action definitions.
- Captures pre-action and post-action state snapshots.

---

## 4. Key Architectural Decisions to Confirm

- [ ] Communication protocol for live action streaming (WebSocket vs Server-Sent Events).
- [ ] Isolation model (Process-level sandboxing vs Docker containers vs Git branch worktree isolation).
