# Data Model & Domain Entities — REWIND

> **Document Version**: 1.0.0 — Domain Data Model Specification  
> **Status**: Complete / Approved  
> **Event**: CUTC: Transform Hackathon 2026  
> **Repository Target**: `~/Documents/Dev/Projects/rewind`  

---

## 1. Domain Entities & Relationships

```
┌─────────────────┐       1:N       ┌─────────────────┐       1:N       ┌─────────────────────┐
│  AgentSession   ├────────────────►│    ActionLog    ├────────────────►│  ActionDependency   │
└────────┬────────┘                 └────────┬────────┘                 └─────────────────────┘
         │ 1:N                               │ 1:1
         ▼                                   ▼
┌─────────────────┐                 ┌─────────────────┐
│   Checkpoint    │                 │ InverseOperation│
└─────────────────┘                 └─────────────────┘
```

---

## 2. Entity Schemas

### 2.1 `AgentSession`
* `id`: UUID (Primary Key)
* `goal_prompt`: String (User intent)
* `workspace_root`: String (Absolute path)
* `status`: Enum (`SESSION_CREATED`, `RUNNING`, `WAITING_FOR_APPROVAL`, `PAUSED`, `ROLLING_BACK`, `COMPLETED`, `FAILED`, `ROLLED_BACK`)
* `created_at`: UTC Timestamp
* `updated_at`: UTC Timestamp

### 2.2 `ActionLog`
* `id`: UUID (Primary Key)
* `session_id`: Foreign Key (`AgentSession.id`)
* `step_index`: Integer
* `tool_name`: String
* `arguments`: JSONB
* `reasoning`: Text
* `risk_score`: Enum (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
* `reversibility_class`: Enum (`FULLY_REVERSIBLE`, `STATE_RESTORABLE`, `PARTIALLY_REVERSIBLE`, `IRREVERSIBLE`)
* `pre_state_ref`: JSONB (Git commit hash, file preimage hash)
* `post_state_ref`: JSONB (Diff summary, affected paths)
* `status`: Enum (`COMMITTED`, `REVERTED`, `FAILED`, `SKIPPED`)
* `verification_result`: Enum (`PASSED`, `FAILED`, `SKIPPED`)

### 2.3 `Checkpoint`
* `id`: UUID (Primary Key)
* `session_id`: Foreign Key (`AgentSession.id`)
* `step_index`: Integer
* `git_commit_hash`: String
* `db_savepoint_name`: String (Optional)
* `filesystem_tree_hash`: String
* `integrity_hash`: String (SHA-256 Merkle root)
* `created_at`: UTC Timestamp

### 2.4 `InverseOperation`
* `id`: UUID (Primary Key)
* `action_id`: Foreign Key (`ActionLog.id`)
* `inverse_tool_name`: String
* `inverse_arguments`: JSONB
* `execution_order`: Integer
