# UX & Time Machine Design Specification — REWIND

> **Status**: Draft / Pending Detailed Specification  

---

## 1. Overview

Design requirements for the Time Machine interface built with Next.js, Tailwind CSS, and Framer Motion.

---

## 2. Key Interface Views

1. **Timeline Navigator**: Horizontal / vertical interactive scrubber showing agent steps, checkpoints, and risk flags.
2. **Action Inspector**: Detailed card view of prompt intent, executed tool call, parameters, risk score, and inverse recipe.
3. **State Diff View**: Monaco / visual code diff showing exact file and state mutations before vs after selected step.
4. **Rollback Control Panel**: Visual confirmation dialog for rewinding to selected step or selective dependency branch.
