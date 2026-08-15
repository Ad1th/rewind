# UX & Time Machine Design Specification — REWIND

> **Document Version**: 1.0.0 — UX & Time Machine Design Specification  
> **Status**: Complete / Approved  
> **Event**: CUTC: Transform Hackathon 2026  
> **Repository Target**: `~/Documents/Dev/Projects/rewind`  

---

## 1. Product Aesthetic & Design Philosophy

REWIND is designed to feel like **Linear + Git + a Time Machine for AI agents**—not a generic conversational AI chatbot dashboard.

### Core Product Persona & Visual Principles
1. **High Information Density**: Clean, precision-engineered developer interface prioritizing visual code diffs, timeline scrubbers, and risk badges over conversational fluff.
2. **Deterministic Control**: The user feels in absolute command of agent operations, with instant visual feedback and frictionless rollback mechanisms.
3. **30-Second Judge Impression**: A hackathon evaluator must immediately understand the core value proposition (Ctrl+Z for AI agents) within 30 seconds of looking at the screen.

---

## 2. Layout & Key Interface Regions

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [REWIND] Session: #8f92a1  | Workspace: ~/dev/my-project  | Mode: HIGH-SAFETY  | Status: RUNNING (Step 4) │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                         │
│  ┌──────────────────────────────────────────────────┐  ┌─────────────────────────────────────────────┐  │
│  │               TIMELINE SCRUBBER                  │  │             ACTION INSPECTOR                │  │
│  │ [Step 1: OK] ── [Step 2: OK] ── [Step 3: FAILED] │  │ Tool: fs.write_file                         │  │
│  │    (Chk 1)          (Chk 2)        ▲ (Selected)  │  │ Target: src/index.ts                        │  │
│  │                                    │             │  │ Risk: HIGH (File Edit)                      │  │
│  │ [◄ PREV]  [PAUSE]  [NEXT ►]  [ ↺ REWIND HERE ]   │  │ Verification: FAILED (Syntax Error)         │  │
│  └──────────────────────────────────────────────────┘  └─────────────────────────────────────────────┘  │
│                                                                                                         │
│  ┌───────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                MONACO VISUAL STATE DIFF VIEWER                                    │  │
│  │  BEFORE (Step 2 Checkpoint)                 │  AFTER (Step 3 Proposed Action)                      │  │
│  │  1: import { db } from './config';          │  1: import { db } from './config.old';                │  │
│  │  2: export function init() { ... }          │  2: export function init() { ... }                    │  │
│  └───────────────────────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Interface Components

### 3.1 Time Machine Timeline Scrubber
- **Interactive Scrubber Axis**: Horizontal linear track displaying chronologically ordered action steps and milestone checkpoints.
- **Node Status Indicators**:
  * `SUCCESS` (Emerald Dot `#10B981`)
  * `FAILED` (Rose Dot `#EF4444`)
  * `WAITING_APPROVAL` (Amber Pulsing Pill `#F59E0B`)
  * `REVERTED` (Purple Strikethrough `#8B5CF6`)
- **Scrubber Controls**: Jump to First, Previous Step, Pause/Play Agent, Next Step, **REWIND TO SELECTED STEP** (`Ctrl+Z`).

### 3.2 Action Inspector Panel
Displays exhaustive metadata for the active or selected step:
- **Action Intent**: Natural language summary from LLM reasoning.
- **Tool & Parameters**: Formatted JSON viewer displaying target path, arguments, and execution environment.
- **Risk Badge**: Prominent pill displaying risk score (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) with safety rationale.
- **Reversibility Badge**: Indicates `FULLY_REVERSIBLE`, `STATE_RESTORABLE`, `PARTIALLY_REVERSIBLE`, or `IRREVERSIBLE`.
- **Verification Evidence**: Output from automated syntax compiler or linter (`npx tsc --noEmit`).

### 3.3 Monaco Visual State Diff Viewer
- **Side-by-Side Code Diff**: Displays exact line-by-line file changes between pre-action snapshot and post-action state.
- **Git Commit Delta**: Displays Git tree commit hashes and uncommitted file count.
- **PostgreSQL Row Delta**: Visual table viewer showing inserted/updated/deleted row deltas.

### 3.4 Rollback Confirmation Modal
When the user clicks **REWIND TO SELECTED STEP**:
- **Target Milestone**: Clearly states target step index and checkpoint timestamp.
- **Impact Warning**: Lists downstream actions that will be undone (e.g. *"This will revert 3 steps across 2 files"*).
- **Confirmation Action**: High-contrast purple `[CONFIRM REWIND (CTRL+Z)]` button.

---

## 4. End-to-End User Interaction Flow

```
[ User Enters Goal Prompt ]
           │
           ▼
[ Live Plan Streamed to UI ] ──► (User reviews plan steps)
           │
           ▼
[ Agent Executes Step 1 & 2 ] ──► (Timeline populates green nodes; live diffs update)
           │
           ▼
[ Agent Executes Step 3 (Flawed) ] ──► (Red node appears; Verification Failure alert pops up)
           │
           ▼
[ User Inspects Step 3 Diff ] ──► (Monaco editor highlights invalid import)
           │
           ▼
[ User Clicks Step 2 Node ] ──────► (Scrubber highlights target checkpoint)
           │
           ▼
[ User Clicks REWIND (Ctrl+Z) ] ──► (Rollback confirmation dialog opens)
           │
           ▼
[ Rollback Executed (<500ms) ] ────► (Timeline animates reverted nodes; file diffs restore)
           │
           ▼
[ Agent Resumes Execution ] ─────► (Agent executes corrected path to goal completion)
```

---

## 5. Visual Design Tokens & Design System

```css
:root {
  /* Color Palette - Dark Slate Precision */
  --bg-dark: #090D16;
  --surface-container: #111827;
  --surface-card: #1F2937;
  --border-subtle: #374151;
  --text-primary: #F9FAFB;
  --text-secondary: #9CA3AF;
  
  /* Status & Risk Accents */
  --color-success: #10B981;    /* Emerald - Low Risk / Passed */
  --color-medium: #F59E0B;     /* Amber - Medium Risk / Warning */
  --color-high: #F97316;       /* Orange - High Risk */
  --color-critical: #EF4444;   /* Rose - Critical / Verification Failed */
  --color-reverted: #8B5CF6;   /* Purple - Rollback / Reverted State */
  
  /* Typography */
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}
```

---

## 6. Micro-Interactions & Motion Choreography

1. **Timeline Node Insertion**: New action steps slide smoothly onto the timeline track from the right using a Framer Motion spring transition (`stiffness: 300, damping: 25`).
2. **Rollback Animation**: When a rollback is confirmed, downstream nodes fade to 40% opacity with a purple diagonal strikethrough animation as the scrubber head slides back to the target checkpoint.
3. **Visual Diff Pulse**: Changed lines in the Monaco diff viewer briefly flash green (additions) or red (deletions) upon step selection.

---

## 7. Keyboard Navigation & Accessibility

- **Global Shortcuts**:
  * `Ctrl+Z` / `Cmd+Z`: Trigger Rollback Modal for currently selected timeline step.
  * `Spacebar`: Pause / Resume active agent execution.
  * `Left Arrow` (`←`): Select previous timeline step.
  * `Right Arrow` (`→`): Select next timeline step.
  * `Esc`: Close modals / inspect panels.
- **Accessibility**: High contrast ratios (min 4.5:1), full keyboard tab navigation, `aria-live` screen reader announcements for incoming WebSocket action events.

---

## 8. Responsive & Judge Viewport Target

- **Primary Target Display**: Optimized for 1440x900 / 1920x1080 desktop screens (Hackathon Judging Displays).
- **30-Second Judging Highlight**: A persistent **"Demo Scenario Preset"** button sits in the top header, allowing judges to trigger the canonical flaw-and-rollback demonstration in one click.
