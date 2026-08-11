# Security & Sandboxing Specification — REWIND

> **Status**: Draft / Pending Detailed Specification  

---

## 1. Overview

Details isolation mechanisms, credential safety, filesystem permission boundaries, and destructive command interception.

---

## 2. Threat Model & Boundaries

- **Forbidden Actions**: Arbitrary root shell calls, external unauthorized network egress, permanent file deletion outside working tree.
- **Sandboxing**: Restricted working directory jail, Git worktree isolation, or Docker containerized execution.
- **Key Safety**: API credentials strictly injected via environment variables; never logged in action persistence layer.
