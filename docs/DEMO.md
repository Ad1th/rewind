# Hackathon Demo Plan — REWIND

> **Document Version**: 1.0.0 — Hackathon Demo Choreography & Script  
> **Status**: Complete / Approved  
> **Event**: CUTC: Transform Hackathon 2026  
> **Repository Target**: `~/Documents/Dev/Projects/rewind`  

---

## 1. Demo Narrative & Core Thesis

### The Problem
Autonomous AI coding agents are incredibly powerful, but they operate without a safety net. A single flawed tool call mid-way through a 10-step task can delete source files, corrupt database tables, or introduce breaking dependencies—forcing developers to perform manual git resets that wipe uncommitted work or attempt prompt-based "undo" commands that hallucinate.

### The REWIND Solution
**REWIND is Ctrl+Z for AI agents.** It introduces a deterministic runtime safety net that intercepts agent tool calls, creates zero-overhead state snapshots, builds a live Action Dependency DAG, verifies environment invariants, and enables instant visual state rewinds without invoking the LLM to fix its own mistakes.

---

## 2. Canonical Hackathon Demo Scenario

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       DEMO SCENARIO CHOREOGRAPHY                                       │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Initial State: Workspace with legacy config file `config.old.json` and Postgres DB.                     │
│ Goal Prompt  : "Clean up project workspace, migrate config to `src/config.ts`, and remove obsolete files." │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Step 1: Agent creates `src/config.ts`                ──► [SUCCESS] (Checkpointed)                      │
│ Step 2: Agent deletes `config.old.json`              ──► [HIGH RISK - APPROVED] (Snapshot Saved)       │
│ Step 3: Agent edits `src/app.ts` (Broken Import)     ──► [FLAWED STEP - VERIFICATION FAILED]           │
│                                                                                                        │
│ ──► USER CLICKS "REWIND TO STEP 1" (CTRL+Z)                                                            │
│ ──► REWIND Restores Filesystem & Postgres in <500ms (100% Deterministic, No LLM)                        │
│ ──► Agent Resumes Execution along Corrected Path                                                       │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 3-Minute Demo Timeline & Choreography

| Timestamp | Phase | Presenter Action | Visual Screen Action | Verbal Highlights |
| :--- | :--- | :--- | :--- | :--- |
| **0:00 – 0:20** | **Hook & Problem** | Introduce REWIND concept. | Display side-by-side: Raw Agent chaos vs REWIND Time Machine UI. | *"AI agents are editing production code and databases, but they lack Ctrl+Z. When an agent breaks your project, you're stuck cleaning up manually."* |
| **0:20 – 0:40** | **Task Trigger** | Click **"Run Cleanup Task"**. | UI populates session, goal prompt, and initial live DAG node. | *"Watch REWIND intercept every tool call in real time, capturing Git worktrees and Postgres savepoints."* |
| **0:40 – 1:10** | **Execution & Flaw** | Agent executes Steps 1, 2, 3. Step 3 introduces a breaking import. | Live timeline streams steps. Step 3 turns **RED** (`VERIFICATION_FAILED`). | *"Step 3 introduced a broken import. Notice how REWIND's deterministic verification engine caught the error before committing."* |
| **1:10 – 1:40** | **Visual Diff Inspection** | Select Step 3 node. | Monaco Diff Viewer shows split-pane file diff highlighting broken line. | *"In the Time Machine UI, we can inspect the exact pre-state vs post-state code diff and database delta."* |
| **1:40 – 2:20** | **The REWIND Moment** | Click **"REWIND TO STEP 1"** (`Ctrl+Z`). | Confirmation modal pops up; timeline nodes slide back; file diffs restore instantly (<500ms). | *"We don't ask the LLM to hallucinate an undo. We hit Ctrl+Z. REWIND deterministically rolls back the filesystem and database in under 500 milliseconds."* |
| **2:20 – 2:45** | **Agent Resumes** | Click **"Resume Execution"**. | Agent runs Step 3' cleanly with correct import; timeline turns green (`COMPLETED`). | *"The workspace is restored to 100% clean fidelity, and the agent completes the task safely."* |
| **2:45 – 3:00** | **Closing Punchline** | Final slide / repo highlight. | Show REWIND architecture diagram and Github repo link. | *"We don't need agents that never make mistakes. We need agents whose mistakes don't become disasters."* |

---

## 4. Judging Alignment Matrix

| Hackathon Criterion | Demo Feature / Moment | Technical Proof Point |
| :--- | :--- | :--- |
| **Technical Execution** | Live multi-domain rollback (Filesystem + PostgreSQL). | Deterministic state restoration executed in $<500\text{ms}$ without LLM prompt calls. |
| **UX & Intuition** | Interactive Time Machine Timeline Scrubber & Visual Monaco Diff. | Instant split-pane code diff inspection and single-click `Ctrl+Z` rollback button. |
| **Creativity & Originality** | Transactional safety proxy layer for LLM agents. | Novel application of transactional DAG concepts to autonomous agent runtimes. |

---

## 5. Fail-Safe Fallback Mechanics

To guarantee zero live demo failures during judging:
1. **Local Deterministic LLM Mock Mode**: A secondary toggle (`--demo-mock-mode`) reads pre-cached OpenAI responses with exact step timing if network latency fluctuates.
2. **Pre-Seeded Workspace**: The target workspace directory is pre-seeded with a one-line reset command (`npm run demo:reset`).

---

## 6. Word-for-Word Presenter Script

> *"Hi everyone. We are building the future of autonomous software engineering with AI agents. But right now, working with AI agents feels like walking a tightrope without a net. When an agent refactors your codebase and makes a mistake on step 4, your uncommitted work is destroyed, or worse, your database is corrupted.*
> 
> *Today, we're introducing **REWIND: Ctrl+Z for AI agents**.*
> 
> *(Click Run Demo)*
> 
> *Here, our agent is tasked with cleaning up a legacy codebase and updating database configurations. As the agent plans and executes, REWIND sits between the LLM and the OS. Every tool call is intercepted, checked for risk, and checkpointed using Git worktrees and Postgres savepoints.*
> 
> *(Point to Red Step 3)*
> 
> *Look at Step 3. The agent edited `app.ts` and introduced a breaking import. REWIND's deterministic verification engine immediately flagged the error and paused execution.*
> 
> *(Click Step 3 & Show Monaco Diff)*
> 
> *In our Time Machine interface, we can inspect the exact visual code diff before and after the step. We see the mistake right here.*
> 
> *(Click REWIND TO STEP 1)*
> 
> *Instead of prompting the LLM and hoping it doesn't hallucinate an undo script, we simply press Ctrl+Z.*
> 
> *In under 500 milliseconds, REWIND deterministically restores the filesystem and database to Step 1.*
> 
> *(Click Resume)*
> 
> *The agent receives the clean environment context and completes the refactoring flawlessly.*
> 
> ***We don't need agents that never make mistakes. We need agents whose mistakes don't become disasters.***
> 
> *Thank you!"*
