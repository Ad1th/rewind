# Product Requirements Document (PRD) — REWIND

> **Document Version**: 1.0.0 — Product Definition Complete  
> **Status**: Complete / Draft — Product Definition Complete  
> **Event**: CUTC: Transform Hackathon 2026  
> **Target Deadline**: August 15, 2026 at 9:30 PM IST  
> **Repository Target**: `~/Documents/Dev/projects/rewind`  

---

## 1. Executive Summary

**REWIND** is a dedicated safety, reliability, and transaction runtime for autonomous AI agents. As AI agents evolve from passive conversational assistants into active execution engines capable of mutating filesystems, executing Git operations, altering database schemas, and interacting with external APIs, the risk of destructive, uncoordinated, or erroneous side-effects escalates dramatically.

Existing AI agent frameworks execute side-effects directly against real environments with no safety net. When an agent commits a flawed step (e.g. deleting source files, corrupting a database table, or applying broken code refactors), recovery currently requires manual human intervention or crude git resets that destroy uncommitted work.

**REWIND solves this fundamental flaw by introducing Ctrl+Z for AI agents.**

REWIND wraps agent execution in deterministic transaction boundaries. It intercepts every agent tool call, evaluates risk, captures pre-execution state snapshots, builds a Directed Acyclic Graph (DAG) of action dependencies, generates inverse operations, verifies post-execution invariants, and provides single-click, deterministic state rollbacks via a visual Time Machine interface.

---

## 2. Product Vision

To become the standard safety layer and transactional engine for autonomous software agents—enabling developers and organizations to grant AI agents high operational authority with zero fear of irreversible damage.

In the REWIND paradigm:
- AI agents operate with explicit, transparent, and auditable transaction boundaries.
- Every state-changing action is preceded by automatic, lightweight checkpointing.
- Every past action can be inspected, verified, and deterministically undone without relying on the LLM to "hallucinate" an undo strategy.

---

## 3. Problem Statement

Autonomous AI agents suffer from three critical safety failures when executing multi-step tasks in software environments:

1. **Irreversibility of Side-Effects**: Standard agent runtimes execute tool calls sequentially without transaction boundaries. A single erroneous tool call mid-way through a 10-step plan corrupts the environment state, requiring manual cleanup.
2. **LLM Hallucination of Rollback**: Relying on an LLM to "fix" its own mistakes by issuing corrective prompts often compounds errors, as the model lacks exact knowledge of prior binary/text environment states.
3. **Lack of Provenance & Action Visibility**: Developers cannot easily inspect why an agent took an action, what exact state changes resulted, what downstream dependencies were created, or what risk level was introduced.

---

## 4. Why Existing Approaches Are Insufficient

| Approach | How it Works | Why it Fails for Autonomous AI Agents |
| :--- | :--- | :--- |
| **Manual Git Reset (`git reset --hard`)** | Developer manually wipes uncommitted changes. | Destroys human work alongside agent work; cannot revert database mutations; zero granular step-level control. |
| **Prompt-Based Correction** | Asking the agent to "undo what you just did". | Non-deterministic; the LLM frequently hallucinates prior file contents, misses deleted files, or introduces new bugs. |
| **Simple Human-in-the-Loop Approval** | Pausing before *every* tool call for human confirmation. | Destroys agent autonomy; creates severe cognitive friction; humans approve dangerous actions anyway due to fatigue. |
| **Read-Only Agent Mode** | Restricting agents to code analysis without tool side-effects. | Prevents agents from executing useful work (refactoring, migration, testing, environment cleanup). |

---

## 5. Target Users

1. **Software Engineers & Developers**: Building, testing, or utilizing autonomous coding agents for codebase refactoring, migrations, and automated bug fixes.
2. **AI Agent Developers & Researchers**: Framework creators needing a reliable transactional execution wrapper and state sandbox.
3. **Hackathon Judges & Technical Evaluators**: Assessing agent safety, runtime control, and novel UX patterns in modern AI tooling.

---

## 6. User Personas

### Persona A: Alex — Senior Full-Stack Engineer
- **Need**: Wants to delegate tedious multi-file refactoring and database schema updates to an AI agent.
- **Pain Point**: Terrified that the agent will delete essential configuration files, corrupt local Postgres tables, or pollute the Git tree.
- **Goal**: Run the agent with total confidence, inspect live diffs step-by-step, and press Ctrl+Z immediately if the agent strays off target.

### Persona B: Maya — Hackathon Judge / Technical Evaluator
- **Need**: Evaluating technical sophistication, originality, and UX of hackathon submissions.
- **Pain Point**: Bored of thin LLM wrappers and generic chat interfaces.
- **Goal**: Witness a robust, deterministic system that intercepts agent side-effects, handles real environment state snapshots (filesystem, git, DB), and visually demonstrates atomic rollbacks in under 30 seconds.

---

## 7. Core Product Promise

**REWIND guarantees that no autonomous AI agent action can permanently corrupt a managed workspace without explicit, auditable trace and deterministic rollback capability.**

If an agent makes a mistake across 5 sequential steps, REWIND allows the user or runtime to rewind the environment back to step 2 with 100% state fidelity—reverting files, git commits, and database mutations deterministically without invoking the LLM.

---

## 8. Product Principles

1. **Deterministic Over Generative Rollback**: Rollback is executed by a deterministic software runtime (file diff engines, Git tree restoration, DB transaction savepoints, inverse scripts)—NEVER by asking an LLM to generate an undo script.
2. **State Transparency**: Every action must record pre-state evidence, post-state evidence, risk score, and explicit diffs.
3. **Sandboxed Execution**: Agent tools execute inside controlled boundaries with strict permission checks.
4. **Frictionless Intuition**: The interface must look and feel like a modern, dynamic Time Machine with scrubber controls, risk badges, and visual code diffs.
5. **Honest Reversibility**: Never pretend external, non-restorable side-effects (e.g. sent HTTP POSTs, emails) are reversible; explicitly classify, warn, and audit them.

---

## 9. Core User Journey

```
[ User defines Goal & Workspace ] 
               │
               ▼
[ Agent generates Structured Plan ]
               │
               ▼
┌───────────────────────────────────────────────────────────┐
│               REWIND RUNTIME EXECUTION LOOP               │
│                                                           │
│  1. Intercept Tool Call                                   │
│  2. Classify Risk & Evaluate Policy                       │
│  3. Capture Pre-State Checkpoint                           │
│  4. Execute Tool in Sandbox                               │
│  5. Verify Invariants & Post-State Evidence                │
│  6. Register Inverse Recipe & Update Dependency DAG       │
│  7. Stream Action & State Diff to Time Machine UI         │
└─────────────────────────────┬─────────────────────────────┘
                              │
               ┌──────────────┴──────────────┐
               │                             │
    [ Normal Execution ]            [ Flawed / Risky Step ]
               │                             │
               ▼                             ▼
   [ Next Step in Plan ]             [ User Clicks REWIND ]
                                             │
                                             ▼
                                  [ Deterministic State ]
                                  [  Restoration Engine  ]
                                             │
                                             ▼
                                  [ Agent Resumes from  ]
                                  [  Restored Checkpoint]
```

---

## 10. MVP Feature Set Overview

- **Workspace Management**: Local workspace sandboxing covering directory tree, Git repository state, and local PostgreSQL instance.
- **Structured Agent Planning**: Structured plan generation breaking user instructions into discrete, inspectable steps.
- **Action Interception & Provenance Engine**: Real-time tool interceptor capturing tool metadata, arguments, timestamps, and execution context.
- **Deterministic Checkpoint Engine**: Automatic creation of lightweight environment state snapshots before state-modifying actions.
- **Risk Analysis Module**: Heuristic and rule-based policy engine assigning risk scores (LOW, MEDIUM, HIGH, DESTRUCTIVE/IRREVERSIBLE) to proposed tools.
- **Verification Engine**: Automated post-execution checks (file existence, syntax validation, linter/test runs, schema integrity).
- **Inverse Operation & DAG Engine**: Automatic mapping of inverse functions (e.g. `write_file` → `restore_original_file_content`, `create_table` → `drop_table`) and tracking parent-child dependencies.
- **Deterministic Rollback Engine**: One-click restoration of workspace state back to any selected historical checkpoint.
- **Time Machine Visual UI**: Next.js interface with step timeline scrubber, risk highlights, state diff viewer, and rollback trigger controls.

---

## 11. Workspace Model

A **Workspace** in REWIND is the isolated operational domain granted to an AI agent session.

- **Filesystem Context**: Target working directory path.
- **Git Context**: Dedicated Git branch or isolated Git worktree preventing pollution of the user's primary working branch.
- **Database Context**: Dedicated PostgreSQL schema or transaction savepoint namespace.
- **Isolation Guarantee**: All tool executions are strictly scoped to the defined Workspace boundary; path traversal outside the workspace root is rejected by the runtime.

---

## 12. Agent Planning

Before executing tool calls, the agent runtime prompts the LLM to emit a **Structured Plan**.

- A Plan consists of an ordered sequence of intended **Actions** with stated goals and target tools.
- The Plan is rendered in the UI, allowing the user to view the agent's proposed trajectory before execution begins.
- As execution proceeds, the Plan status updates dynamically (PENDING → IN_PROGRESS → COMPLETED / REVERTED).

---

## 13. Action Interception

The **REWIND Interceptor** sits directly between the LLM and the execution environment.

```
  [ LLM Output ] ──(Tool Call Request)──► [ REWIND Interceptor ]
                                                   │
                                                   ├── 1. Validate Schema
                                                   ├── 2. Evaluate Risk Policy
                                                   ├── 3. Trigger Pre-Checkpoint
                                                   ▼
                                         [ Sandboxed Tool Exec ]
```

- When the LLM requests a tool execution, execution is paused synchronously.
- The Interceptor extracts tool name, arguments, and declared intent.
- Pre-execution hooks run prior to passing control to the underlying tool wrapper.

---

## 14. Checkpoints

A **Checkpoint** is an immutable, point-in-time snapshot of the Workspace state.

- **Automatic Checkpoints**: Created automatically by REWIND prior to executing any action classified as MEDIUM, HIGH, or DESTRUCTIVE risk.
- **Manual Checkpoints**: Triggered explicitly by the user via the UI at any milestone.
- **State Coverage**: Captures file contents/hashes, Git commit HEAD pointers, and PostgreSQL transaction savepoints/schema states.

---

## 15. Action Timeline

The **Action Timeline** is the visual and structural backbone of REWIND.

- Renders an ordered, interactive timeline of every intercepted Action.
- Displays key metadata per step: Action ID, Tool Name, Intent, Risk Level, Execution Duration, Verification Status, and Checkpoint ID.
- Allows jumping to any step to inspect pre-state vs post-state diffs or initiate a Rollback.

---

## 16. Risk Analysis

Every proposed Action is evaluated against a pre-defined safety and risk policy before execution.

### Risk Classifications

| Risk Level | Definition | System Behavior |
| :--- | :--- | :--- |
| **LOW** | Read-only operations (e.g. `read_file`, `list_dir`, `db_query_select`). | Auto-approve; log provenance; no full snapshot needed. |
| **MEDIUM** | Standard non-destructive modifications (e.g. `create_file`, `append_file`, `db_insert`). | Create Checkpoint; execute tool; register inverse recipe. |
| **HIGH** | Broad modifications or structural changes (e.g. `overwrite_file`, `git_commit`, `db_alter_table`). | Create Checkpoint; perform verification check; log detailed evidence. |
| **DESTRUCTIVE / IRREVERSIBLE** | Permanent deletion or external side-effects (e.g. `delete_file`, `git_drop_branch`, `db_drop_table`, `http_post`). | Create Checkpoint; enforce user confirmation prompt (if configured); log permanent audit flag. |

---

## 17. Verification

After tool execution, the **Verification Engine** runs automated assertions to validate environment integrity:

- **Syntax & Format Validation**: Ensures modified `.json`, `.py`, `.ts`, or `.sql` files retain valid syntax.
- **Linter / Test Verification**: Optionally runs micro-checks (e.g. `python -m py_compile` or micro test runners) to detect immediate breaking changes.
- **State Invariant Checks**: Verifies that required files still exist and database foreign keys remain consistent.
- If verification fails, REWIND flags the step as **FAILED_VERIFICATION** in the UI and prompts for automatic rollback.

---

## 18. Reversibility Taxonomy

REWIND explicitly categorizes all agent actions into four strict reversibility tiers. **REWIND never claims that arbitrary external APIs or physical side-effects can be undone.**

```
                                  ACTION PROPOSED
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │                                               │
          Internal State Mutation                      External Side-Effect
                 │                                               │
       ┌─────────┴─────────┐                           ┌─────────┴─────────┐
       │                   │                           │                   │
Full Inverse Exists   Snapshot Coverable           Partial Reversal    Irreversible
       │                   │                           │                   │
  ▼ TIER 1            ▼ TIER 2                    ▼ TIER 3            ▼ TIER 4
Fully Reversible   State-Restorable            Partially Reversible   Irreversible
 (Inverse Exec)    (Checkpoint Reset)           (Compensating Exec) (Audit & Warn)
```

### Tier 1: Fully Reversible Actions
- **Definition**: Actions with precise, deterministic mathematical/logical inverse operations.
- **Examples**:
  - `create_file(path)` → Inverse: `delete_file(path)`
  - `rename_file(old, new)` → Inverse: `rename_file(new, old)`
  - `db_insert(table, row_id)` → Inverse: `db_delete(table, row_id)`
- **Rollback Mechanism**: Direct execution of registered inverse recipe.

### Tier 2: State-Restorable Actions
- **Definition**: Complex state mutations where calculating a granular inverse is inefficient, but complete pre-state snapshot restoration is guaranteed.
- **Examples**:
  - Multi-line file edits / complex refactoring (`write_file`)
  - Git commits or branch merges
  - Batch database updates (`UPDATE table SET ...`)
- **Rollback Mechanism**: Restoring exact file contents from pre-checkpoint, resetting Git HEAD to pre-checkpoint hash, or rolling back Postgres transaction savepoint.

### Tier 3: Partially Reversible Actions
- **Definition**: Actions where primary local state changes can be undone, but secondary artifacts (logs, build caches, temporary IDs) remain.
- **Examples**:
  - Running a build command that generates local build cache files alongside updated output.
  - Creating a Git commit and pushing to a local temporary branch.
- **Rollback Mechanism**: Local state snapshot restore + cleanup of generated artifacts; user alerted to residual side-effects.

### Tier 4: Irreversible Actions
- **Definition**: Operations involving external network egress, third-party state mutation, or physical side-effects where technical state undo is impossible.
- **Examples**:
  - Sending an HTTP POST request to an external API endpoint.
  - Posting a comment on a remote GitHub Issue/PR.
  - Sending an email or webhook message.
- **Handling Mechanism**:
  1. System detects action as **IRREVERSIBLE**.
  2. Enforces explicit user UI confirmation before execution (or blocks execution if policy mandates).
  3. Records permanent audit log entry with warning badge in Timeline.
  4. Explicitly informs user: *"This action cannot be undone by REWIND Ctrl+Z."*

---

## 19. Rollback Engine

The **Rollback Engine** provides deterministic, atomic state restoration.

- **Deterministic Execution**: Uses system level file I/O, Git reset commands, and SQL rollback transactions—NOT LLM generation.
- **Rollback Modes**:
  - **Single-Step Rollback**: Reverts only the latest executed action.
  - **Checkpoint Target Rollback**: Reverts all workspace state changes back to a selected historical Checkpoint.
  - **Cascading Dependency Rollback**: Automatically identifies downstream dependent actions in the DAG and undoes them in reverse topological order.
- **Atomicity Guarantee**: If rollback execution fails mid-way, REWIND halts and reports an error without leaving workspace state half-reverted.

---

## 20. Action Inspector

The **Action Inspector** is a dedicated UI drawer in the Time Machine interface.

When a user clicks any Action in the Timeline, the Inspector displays:
- **Prompt Intent**: The original LLM reasoning/user goal that spawned the action.
- **Tool Details**: Exact tool function signature and JSON arguments.
- **Risk & Policy Score**: Risk badge (LOW/MEDIUM/HIGH/DESTRUCTIVE), trigger policies, and reversibility tier.
- **Evidence & Verification**: Post-execution check results, console output, and invariant status.
- **Inverse Recipe**: The registered inverse command ready for execution upon rollback.

---

## 21. State / Diff Viewer

The **State / Diff Viewer** provides side-by-side or inline visual code diffs for all file and database mutations.

- **File Diffs**: Visual red/green syntax-highlighted diffs comparing pre-action vs post-action file state.
- **Database Diffs**: Tabular record diff showing inserted, updated, or deleted database rows.
- **Git Diffs**: Visual display of git status and patch differences.

---

## 22. Supported Initial Tools (MVP Scope)

For the hackathon MVP, REWIND will support a tight, controlled set of robust tools:

### Filesystem Tool Suite
1. `fs_read_file`: Read contents of a file (LOW risk).
2. `fs_write_file`: Write/overwrite contents of a file (MEDIUM/HIGH risk, Tier 2 restorable).
3. `fs_create_file`: Create a new file (MEDIUM risk, Tier 1 inverse: `delete_file`).
4. `fs_delete_file`: Delete a file (DESTRUCTIVE risk, Tier 2 restorable via pre-checkpoint).
5. `fs_list_dir`: List directory contents (LOW risk).

### Git Tool Suite
6. `git_status`: Query working tree state (LOW risk).
7. `git_commit`: Create a git commit snapshot (MEDIUM risk, Tier 1 inverse: `git reset HEAD~1`).
8. `git_create_branch`: Create a new git branch (LOW risk, Tier 1 inverse: `git branch -D`).

### Database Tool Suite (PostgreSQL)
9. `db_query`: Execute SELECT queries (LOW risk).
10. `db_execute`: Execute INSERT/UPDATE/DELETE statement within transaction savepoint (MEDIUM/HIGH risk, Tier 2 restorable via `ROLLBACK TO SAVEPOINT`).

### External / Integration Tool Suite (Demo Only)
11. `github_create_comment`: Post a comment on a GitHub issue (IRREVERSIBLE, Tier 4, requires policy check).

---

## 23. Demo-First Product Design

REWIND is engineered specifically to make its core value proposition understandable to hackathon judges within **30 seconds**.

- **Immediate Visual Impact**: Dark-mode, high-contrast, polished interface featuring a visual timeline scrubber, glowing risk badges, and Monaco-style code diffs.
- **Zero Ambiguity**: The UI explicitly highlights when a bad action occurs, displays the exact visual diff of the damage, and features a prominent, glowing **REWIND (Ctrl+Z)** action button.
- **Deterministic Proof**: Live execution proves that hitting REWIND instantly restores files and database state without waiting for slow LLM re-prompts.

---

## 24. Canonical Hackathon Demo Scenario

### Scenario Title: "The Over-Eager Refactoring Agent"

- **Duration**: ~2 minutes total (core value proven in first 30 seconds).
- **Target Workspace**: A standard Python/TypeScript web application repository connected to a local PostgreSQL database.

### Step-by-Step Demo Script

1. **Initialization (0:00 - 0:15)**:
   - User opens REWIND UI connected to the target project workspace.
   - User issues goal: *"Refactor the user service module to add a new `last_login` timestamp field and clean up legacy helper files."*

2. **Agent Planning & Initial Execution (0:15 - 0:45)**:
   - Agent generates a 5-step Structured Plan.
   - Step 1 (`db_execute`): Agent adds `last_login` column to Postgres table. REWIND captures DB savepoint checkpoint.
   - Step 2 (`fs_write_file`): Agent updates `user_service.py` with new timestamp logic. REWIND captures file checkpoint & verifies syntax.
   - Timeline populates live with green LOW/MEDIUM risk badges.

3. **The Critical Mistake (0:45 - 1:00)**:
   - Step 3 (`fs_delete_file`): Agent mistakenly deletes `config/database.py` thinking it is legacy dead code, along with dropping the `users` table via an erroneous SQL statement.
   - REWIND Interceptor halts, flags risk as **DESTRUCTIVE**, logs pre-state checkpoint, and flags failed verification in the UI with a glowing RED alert badge.

4. **The REWIND Moment (1:00 - 1:20)**:
   - Judge/User sees the red alert on the Timeline.
   - User clicks Step 3 in Timeline → Action Inspector pops up showing evidence: deleted `config/database.py` and dropped table diff.
   - User clicks **REWIND TO STEP 2**.
   - REWIND Rollback Engine executes instantly: restores `config/database.py` file from checkpoint and rolls back DB savepoint.
   - UI updates instantly: Workspace restored cleanly to Step 2 state.

5. **Resumption & Success (1:20 - 1:45)**:
   - User adds a prompt constraint: *"Do not delete database.py; keep legacy config."*
   - Agent resumes execution from Step 2, completes alternative step cleanly, and finishes task.

---

## 25. Non-Goals (Strict Hackathon Scope Control)

To ensure delivery before the August 15, 2026 deadline, the following are **EXPLICIT NON-GOALS**:

- ❌ **No Universal External API Rollback**: We will not attempt to undo arbitrary third-party webhooks, Stripe charges, or cloud API calls.
- ❌ **No Computer Control / GUI Automation**: No OS mouse/keyboard driving or desktop screenshot automation.
- ❌ **No Production Cloud Infrastructure Management**: No AWS/GCP/Kubernetes terraform or cluster mutations.
- ❌ **No Custom Foundation Model Training**: We use off-the-shelf LLMs via structured tool calling.
- ❌ **No Multi-Tenant Enterprise SaaS Auth/Billing**: Focus is strictly on single-user local developer experience and live hackathon judging demo.
- ❌ **No Financial or Physical System Actions**: No banking APIs, trading bots, or IoT control.

---

## 26. Security Requirements

- **SR-001 (Workspace Jail)**: All file I/O tools MUST validate that target paths resolve strictly within the designated Workspace root path. Absolute path traversal (`/etc/passwd`, `../../`) MUST be rejected with a security exception.
- **SR-002 (Credential Redaction)**: API keys, database passwords, and environment secrets MUST be stripped/masked from Action Logs and UI diff streams.
- **SR-003 (Command Sanitization)**: Shell and Git command executions MUST use sanitized arg arrays rather than unescaped shell string concatenation to prevent command injection.

---

## 27. Functional Requirements

### Workspace & Sandboxing
- **FR-001**: System SHALL allow initializing a Workspace tied to a specific local directory path, Git repository branch/worktree, and PostgreSQL connection.
- **FR-002**: System SHALL enforce path containment, blocking any tool execution targeting paths outside the Workspace root.

### Agent Planning & Interception
- **FR-003**: System SHALL parse LLM output into a Structured Plan containing discrete Action steps prior to execution.
- **FR-004**: System SHALL intercept every tool call request before execution, extracting tool name, parameters, and intent.

### Risk Analysis & Policy Engine
- **FR-005**: System SHALL evaluate proposed tool calls against policy rules and assign a Risk Classification (LOW, MEDIUM, HIGH, DESTRUCTIVE/IRREVERSIBLE).
- **FR-006**: System SHALL flag Tier 4 (Irreversible) actions in the UI and require explicit approval policy configuration.

### Checkpointing & Snapshotting
- **FR-007**: System SHALL automatically capture an immutable Checkpoint prior to executing any action classified as MEDIUM, HIGH, or DESTRUCTIVE.
- **FR-008**: System SHALL store file state snapshots efficiently using file hash tracking and content diffs.
- **FR-009**: System SHALL create PostgreSQL transaction savepoints prior to executing database mutation statements.

### Verification & Invariant Checking
- **FR-010**: System SHALL execute post-execution verification checks on modified files (syntax validation, file existence) and record pass/fail status in evidence logs.

### Inverse Operations & Rollback Engine
- **FR-011**: System SHALL automatically synthesize or assign an Inverse Operation recipe for every reversible tool execution.
- **FR-012**: System SHALL construct a Directed Acyclic Graph (DAG) tracking parent-child dependencies across Action logs.
- **FR-013**: System SHALL provide deterministic single-step and checkpoint-target Rollback capabilities, restoring file and database state without invoking an LLM.

### UI & Time Machine Experience
- **FR-014**: System SHALL provide an interactive visual Timeline UI displaying all executed and pending actions with real-time risk badges.
- **FR-015**: System SHALL stream live agent actions, evidence, and state updates over WebSocket connections to the UI.
- **FR-016**: System SHALL display side-by-side syntax-highlighted visual code and database diffs in the State / Diff Viewer.
- **FR-017**: System SHALL provide a prominent REWIND button enabling one-click state restoration to any selected past action or checkpoint.

---

## 28. Non-Functional Requirements

- **NFR-001 (Deterministic Reliability)**: State restoration to a Checkpoint MUST achieve 100% exact byte match for files and exact row state for managed database tables.
- **NFR-002 (Rollback Performance)**: Rollback execution time for a target checkpoint MUST complete in `< 1.0 second` for local workspace files and Postgres savepoints.
- **NFR-003 (UI Responsiveness)**: The Time Machine UI MUST render state updates and timeline additions within `< 100ms` of backend event emit over WebSockets.
- **NFR-004 (Observability & Auditability)**: 100% of intercepted actions, tool arguments, risk scores, execution outcomes, and evidence MUST be persisted to PostgreSQL audit logs.
- **NFR-005 (Fault Isolation)**: A failure in the agent tool execution MUST NOT crash the REWIND control plane or corrupt existing recorded checkpoints.

---

## 29. Acceptance Criteria

### AC-001: Filesystem State Rollback
> **Given** a Workspace containing file `src/app.py` with content `VERSION = 1`,  
> **When** the agent executes `fs_write_file("src/app.py", "VERSION = 2")`,  
> **And** the user triggers `REWIND` to the pre-execution Checkpoint,  
> **Then** REWIND restores `src/app.py` to exact content `VERSION = 1` within 1 second without requesting LLM assistance.

### AC-002: File Deletion Recovery
> **Given** a Workspace containing file `config/db.json`,  
> **When** the agent executes `fs_delete_file("config/db.json")`,  
> **Then** REWIND captures a pre-deletion Checkpoint,  
> **And** when the user clicks `REWIND`, file `config/db.json` is recreated with its exact original content and permissions.

### AC-003: Database Transaction Rollback
> **Given** a PostgreSQL table `users` with 10 rows,  
> **When** the agent executes `db_execute("DELETE FROM users WHERE active = false")` deleting 3 rows,  
> **And** the user triggers `REWIND`,  
> **Then** REWIND rolls back to the pre-statement savepoint, restoring table `users` to exactly 10 rows.

### AC-004: Irreversible Action Warning & Audit
> **Given** an agent proposing tool call `github_create_comment(issue_id=42, text="...")`,  
> **When** the REWIND Interceptor evaluates the action,  
> **Then** it classifies the action as Tier 4 (Irreversible),  
> **And** displays an alert in the UI specifying *"This action cannot be undone by REWIND Ctrl+Z"*,  
> **And** logs a permanent audit entry if executed.

---

## 30. Success Metrics

1. **Rollback Success Rate**: 100% clean state restoration across all supported file and DB tool operations during demo testing.
2. **Demo Time-to-Value**: Hackathon judge understands the core product thesis within `< 30 seconds` of live demo viewing.
3. **Rollback Execution Speed**: Average state rollback execution time `< 500ms`.
4. **Verification Accuracy**: 100% detection of invalid syntax or missing files created during flawed agent steps.

---

## 31. Competitive Landscape / Differentiation

| Feature / Dimension | Standard Agent Runtimes (LangChain, AutoGen) | Traditional Git (`git reset`) | REWIND Transaction Engine |
| :--- | :--- | :--- | :--- |
| **Rollback Capability** | None (or re-prompt LLM) | Full repo wipe (destructive to human work) | **Granular, step-level deterministic rollback** |
| **Database Transaction Safety** | None | None | **Postgres Savepoint & State restore** |
| **Action Provenance & Dependency DAG** | Basic execution logs | None | **Visual DAG + Risk & Evidence tracking** |
| **Reversibility Awareness** | None | None | **4-Tier Taxonomy with Irreversible alerts** |
| **Time Machine UX** | Text chat logs | Terminal CLI | **Interactive visual scrubber + visual code diffs** |

---

## 32. High-Level Product Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         NEXT.JS TIME MACHINE UI                          │
│  (Timeline Scrubber | Action Inspector | Visual Diff Viewer | Ctrl+Z)   │
└────────────────────────────────────▲─────────────────────────────────────┘
                                     │ WebSocket / REST API
┌────────────────────────────────────▼─────────────────────────────────────┐
│                       FASTAPI BACKEND CONTROL PLANE                      │
│                                                                          │
│  ┌────────────────────────┐  ┌───────────────────────┐  ┌─────────────┐  │
│  │ Interceptor & Risk Engine│  │ Verification Engine  │  │ DAG Engine  │  │
│  └───────────┬────────────┘  └───────────┬───────────┘  └──────┬──────┘  │
│              │                           │                     │         │
│  ┌───────────▼───────────────────────────▼─────────────────────▼──────┐  │
│  │                    DETERMINISTIC ROLLBACK ENGINE                    │  │
│  └───────────────────────────────────┬────────────────────────────────┘  │
└──────────────────────────────────────┼───────────────────────────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
  ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
  │ Local Filesystem │       │  Git Repository  │       │  PostgreSQL DB   │
  │    (File Diffs)  │       │ (Worktree/Reset) │       │   (Savepoints)   │
  └──────────────────┘       └──────────────────┘       └──────────────────┘
```

---

## 33. Core Domain Concepts

- **Workspace**: The bounded environment (directory, git branch, DB schema) where the agent executes.
- **Action**: A single discrete tool invocation attempted by the agent.
- **Plan**: A structured sequence of Actions generated by the LLM to achieve a user Goal.
- **Checkpoint**: An immutable snapshot of Workspace state recorded before a state-modifying Action.
- **State Snapshot**: Concrete file hash tree, Git HEAD pointer, or DB savepoint dataset.
- **Provenance**: The complete historical record of why an action occurred, its input prompt, risk score, and execution evidence.
- **Evidence**: Post-execution validation artifacts (console outputs, syntax check results, diff stats).
- **Verification**: Invariant check confirming whether an action succeeded cleanly.
- **Rollback**: The deterministic restoration of Workspace state to a prior Checkpoint.
- **Inverse Operation**: The specific function recipe capable of reversing a Tier 1 action.
- **Tool**: A sandboxed module exposing specific capabilities (FS, Git, DB) to the agent.
- **Policy**: Rules governing risk classification and execution authorization.
- **Risk Assessment**: The calculated risk rating (LOW, MEDIUM, HIGH, DESTRUCTIVE) for a proposed Action.

---

## 34. MVP Scope: Must / Should / Could / Future

### MUST Have (Hackathon Core - Aug 11-15)
- Interceptor wrapping filesystem, Git, and Postgres tool calls.
- Deterministic Checkpoint & Rollback engine for local files and Postgres savepoints.
- 4-Tier Reversibility Taxonomy implementation with Tier 4 Irreversible warnings.
- Next.js Time Machine UI with interactive Timeline, Action Inspector, Visual Diff Viewer, and REWIND button.
- Canonical Refactoring Demo scenario showing live rollback of a flawed agent step.

### SHOULD Have (If ahead of schedule)
- Automated syntax verification runner (`py_compile` / `ts-node` check).
- Selective branch rollback via dependency DAG.

### COULD Have (Nice-to-have visual polish)
- Animated Framer Motion time-travel visual transitions in UI.
- Simulated multi-agent execution view.

### FUTURE (Post-Hackathon Roadmap)
- Full Docker containerized micro-VM execution sandboxing.
- Cloud infrastructure state rollback (AWS CloudFormation / Terraform state undo).
- Production multi-tenant OAuth and enterprise team permission policies.

---

## 35. Technical & Product Risks and Mitigations

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Large File / Deep Repo Snapshot Overhead** | Slows down agent execution if full copies are made. | Use lightweight file hash indexing and track diffs only for mutated files; rely on Git tree objects where possible. |
| **PostgreSQL Savepoint Leaks** | Long-running transactions lock DB resources. | Scope savepoints to active agent session boundaries; auto-commit or rollback upon session completion. |
| **External API Flakiness in Demo** | Third-party service downtime ruins live judging. | Keep core demo dependent strictly on local Filesystem, Git, and PostgreSQL; mock external GitHub API calls if needed. |
| **LLM Latency During Demo** | Long prompt generation delays video / live demo. | Implement pre-cached response triggers or local model fallback option for demo reliability. |

---

## 36. Open Questions / Pending Technical Decisions

- [ ] **Snapshot Storage Engine**: Should file pre-states be stored as raw copies in a temporary `rewind_snapshots/` folder or as internal Git blobs? *(To be resolved in `ARCHITECTURE.md`)*.
- [ ] **Database Migration Handling**: How should REWIND handle DDL schema changes (`ALTER TABLE`) vs DML row changes (`UPDATE/DELETE`) during Postgres rollbacks? *(To be resolved in `DATABASE.md`)*.
- [ ] **WebSocket Protocol Contract**: Standardizing JSON message payload structures for real-time state diff streaming between FastAPI and Next.js. *(To be resolved in `API.md`)*.

---

## 37. Canonical Terminology Quick Reference

- **Action**: Discrete tool call.
- **Plan**: Sequence of planned Actions.
- **Checkpoint**: Saved point-in-time environment snapshot.
- **State Snapshot**: Physical file/DB state data.
- **Provenance**: Lineage, intent, and audit trail of an Action.
- **Evidence**: Output and verification logs of an Action.
- **Verification**: Invariant assertion result.
- **Rollback**: Deterministic state restoration.
- **Inverse Operation**: Logical undo function.
- **Workspace**: Sandboxed working context.
- **Agent Runtime**: Execution engine managing the LLM tool loop.
- **Tool**: Sandboxed capability wrapper.
- **Policy**: Safety rule set.
- **Risk Assessment**: Calculated risk level for an Action.
