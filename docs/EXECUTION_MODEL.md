# Execution & Snapshot Model — REWIND

> **Status**: Draft / Pending Detailed Specification  

---

## 1. Overview

Defines how agent tool executions are sandboxed and how filesystem, git, and database state snapshots are captured efficiently.

---

## 2. Key Architecture Concepts

- **Target Environments**: Local isolated directory, Git worktree, or Docker container.
- **Snapshot Triggers**: Automatic pre-tool snapshot, post-tool snapshot, periodic milestone snapshot.
- **Diff Computation**: Calculating fine-grained file diffs, tree hashes, and database record deltas for UI visualization.
