# Execution & Snapshot Model — REWIND

> **Document Version**: 1.0.0 — Execution & Snapshot Model Specification  
> **Status**: Complete / Approved  
> **Event**: CUTC: Transform Hackathon 2026  
> **Repository Target**: `~/Documents/Dev/Projects/rewind`  

---

## 1. Execution Sandbox Architecture

Every agent tool call in REWIND executes within an isolated **Execution Sandbox**. The sandbox abstracts target environments (OS Filesystem, Git repository, PostgreSQL database) to prevent uncoordinated mutations and ensure zero-copy state snapshotting.

```
                               ┌──────────────────────────────────────────────┐
                               │           Agent Interceptor Layer            │
                               └──────────────────────┬───────────────────────┘
                                                      │ Validated Tool Call
                                                      ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       EXECUTION SANDBOX WRAPPER                                        │
│  ┌─────────────────────────────┐ ┌─────────────────────────────┐ ┌──────────────────────────────────┐  │
│  │   Path Jailing Controller   │ │  Git Worktree Snapshotter   │ │ PostgreSQL Transaction Wrapper   │  │
│  └─────────────────────────────┘ └─────────────────────────────┘ └──────────────────────────────────┘  │
└─────────────────────────────────────────────┬──────────────────────────────────────────────────────────┘
                                              │
                                              ▼
                                 ┌──────────────────────────┐
                                 │ Target Execution Domain  │
                                 │  (FS / Git / Postgres)   │
                                 └──────────────────────────┘
```

---

## 2. Snapshot Mechanisms & Triggers

REWIND uses an **Adaptive Snapshot Engine**:

1. **Pre-Action Snapshot**: Automatically triggered before any `MEDIUM`, `HIGH`, or `CRITICAL` risk action.
   * **Filesystem**: Copies targeted file bytes to `.rewind/snapshots/<hash>` or creates a Git worktree commit (`git commit -m "checkpoint: pre-step-N"`).
   * **PostgreSQL**: Issues `SAVEPOINT rewind_step_N;` within active transaction or records row pre-image JSON.
2. **Post-Action Snapshot & Diff Computation**: Triggered after tool execution completes.
   * Computes line-by-line unified file diffs, Merkle tree root hashes, and SQL row deltas for UI visualization.

---

## 3. Sandboxing & Isolation Rules

- **Filesystem Isolation**: Jailed paths enforce `os.path.realpath` canonicalization. Access outside `session.workspace_root` throws `SecurityBoundaryViolation`.
- **Git Worktree Isolation**: All file operations execute on isolated branch `rewind/session-<id>` inside `.git/rewind-worktrees/session-<id>`.
- **Process Isolation**: Terminal commands run in unprivileged subshells with a 10s synchronous / 60s asynchronous execution timeout.
