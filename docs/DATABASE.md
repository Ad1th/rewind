# Database Specification & DDL — REWIND

> **Document Version**: 1.0.0 — Database Schema & DDL Specification  
> **Status**: Complete / Approved  
> **Database Engine**: PostgreSQL 16+  
> **Repository Target**: `~/Documents/Dev/Projects/rewind`  

---

## 1. DDL Schema Definition

```sql
-- REWIND Relational Database Schema DDL

CREATE TYPE session_status AS ENUM (
  'SESSION_CREATED', 'RUNNING', 'WAITING_FOR_APPROVAL', 'PAUSED', 
  'ROLLING_BACK', 'COMPLETED', 'FAILED', 'ROLLED_BACK'
);

CREATE TYPE risk_score AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');

CREATE TYPE reversibility_class AS ENUM (
  'FULLY_REVERSIBLE', 'STATE_RESTORABLE', 'PARTIALLY_REVERSIBLE', 'IRREVERSIBLE'
);

CREATE TYPE action_status AS ENUM ('COMMITTED', 'REVERTED', 'FAILED', 'SKIPPED');

CREATE TYPE verification_status AS ENUM ('PASSED', 'FAILED', 'SKIPPED');

-- Sessions Table
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  goal_prompt TEXT NOT NULL,
  workspace_root TEXT NOT NULL,
  status session_status NOT NULL DEFAULT 'SESSION_CREATED',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Action Logs Table
CREATE TABLE action_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  step_index INTEGER NOT NULL,
  tool_name VARCHAR(100) NOT NULL,
  arguments JSONB NOT NULL,
  reasoning TEXT,
  risk_score risk_score NOT NULL,
  reversibility_class reversibility_class NOT NULL,
  pre_state_ref JSONB NOT NULL,
  post_state_ref JSONB,
  status action_status NOT NULL DEFAULT 'COMMITTED',
  verification_result verification_status NOT NULL DEFAULT 'PASSED',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT idx_session_step UNIQUE (session_id, step_index)
);

-- Checkpoints Table
CREATE TABLE checkpoints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  step_index INTEGER NOT NULL,
  git_commit_hash VARCHAR(64) NOT NULL,
  db_savepoint_name VARCHAR(100),
  filesystem_tree_hash VARCHAR(64) NOT NULL,
  integrity_hash VARCHAR(64) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Action Dependencies Table (DAG Edges)
CREATE TABLE action_dependencies (
  parent_action_id UUID NOT NULL REFERENCES action_logs(id) ON DELETE CASCADE,
  child_action_id UUID NOT NULL REFERENCES action_logs(id) ON DELETE CASCADE,
  dependency_type VARCHAR(50) NOT NULL DEFAULT 'CAUSAL',
  PRIMARY KEY (parent_action_id, child_action_id)
);

-- Inverse Operations Table
CREATE TABLE inverse_operations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  action_id UUID NOT NULL REFERENCES action_logs(id) ON DELETE CASCADE,
  inverse_tool_name VARCHAR(100) NOT NULL,
  inverse_arguments JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexing Strategy
CREATE INDEX idx_action_logs_session ON action_logs(session_id, step_index);
CREATE INDEX idx_checkpoints_session ON checkpoints(session_id, step_index);
```
