# Database Specification — REWIND

> **Status**: Draft / Pending Detailed Specification  
> **Database**: PostgreSQL  

---

## 1. Relational Entity Overview

Core tables required:
- `sessions`: Agent execution sessions.
- `checkpoints`: Saved state snapshots (Git commits, file trees, DB state).
- `action_logs`: Recorded agent actions (tool name, parameters, execution status, timestamp, risk rating).
- `action_dependencies`: DAG edges mapping cause-and-effect relationships between action logs.
- `inverse_operations`: Inverse execution commands/scripts associated with reversible actions.
- `verifications`: Verification test results, invariant checks, and risk analysis outputs.

---

## 2. Preliminary Schema Outlines

*(Detailed DDL and migration scripts to be defined during technical specification phase.)*
