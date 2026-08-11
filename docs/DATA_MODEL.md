# Data Model & Event Schemas — REWIND

> **Status**: Draft / Pending Detailed Specification  

---

## 1. Core Domain Entities

- `AgentSession`: Represents an active or historical agent execution run.
- `ActionLog`: Immutable record of a tool call attempt and outcome.
- `Checkpoint`: Named or automated snapshot of full environment state.
- `InverseOperation`: Declarative or programmatic inverse execution recipe.
- `DependencyGraph`: Structure mapping directional dependencies between actions.
- `RiskAssessment`: Risk classification score (LOW, MEDIUM, HIGH, DESTRUCTIVE) and rationale.
