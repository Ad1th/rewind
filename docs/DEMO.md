# Hackathon Demo Plan — REWIND

> **Status**: Draft / Pending Detailed Specification  
> **Event**: CUTC: Transform Hackathon 2026  

---

## 1. Demo Concept & Narrative

Showcase an AI agent performing a complex multi-step refactoring / data modification task:
1. Agent starts task in controlled environment.
2. Agent executes initial valid steps (creating files, updating DB records). Checkpoints logged live in Time Machine UI.
3. Agent encounters a risky or flawed decision step (e.g. deleting critical files or introducing breaking changes).
4. REWIND flags risk score and logs action state.
5. User inspects state diff on Time Machine UI and hits **REWIND / CTRL+Z**.
6. REWIND cleanly reverts environment state back to the pre-flawed checkpoint.
7. Agent resumes execution along a corrected trajectory to task completion.

---

## 2. Judging Alignment Map

- **Technical Execution**: Live rollback of filesystem + Git + DB state without side effects.
- **UX & Intuition**: Sleek timeline scrubber with instant visual diffs.
- **Creativity & Originality**: Novel application of transactional mechanics to AI agent safety.
