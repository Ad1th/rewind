# REWIND Documentation Index

This directory contains the core technical specifications, architecture designs, data models, and operational plans for **REWIND**.

## Index of Specifications

| Document | Description | Status |
| :--- | :--- | :--- |
| [**PRD.md**](./PRD.md) | Product Requirements Document: problem statement, scope, user stories & competition strategy | Complete / Approved — Product Definition Complete |
| [**ARCHITECTURE.md**](./ARCHITECTURE.md) | High-level system architecture, subsystem boundaries, data flow & component topology | Complete / Approved — System Architecture Freeze |
| [**AGENT_WORKFLOW.md**](./AGENT_WORKFLOW.md) | LLM provider abstraction, structured tool calls, execution lifecycle & risk hooks | Complete / Approved — Agent Workflow Specification |
| [**ROLLBACK_ENGINE.md**](./ROLLBACK_ENGINE.md) | Invariant engine, inverse action generators, transaction logs & dependency DAG rollback | Pending Specification |
| [**EXECUTION_MODEL.md**](./EXECUTION_MODEL.md) | Sandboxed tool execution, Docker runtime state capture, snapshotting & delta engines | Pending Specification |
| [**DATA_MODEL.md**](./DATA_MODEL.md) | Core domain entities: Checkpoint, ActionLog, StateSnapshot, InverseOperation, DependencyGraph | Pending Specification |
| [**DATABASE.md**](./DATABASE.md) | PostgreSQL schema, indexing strategy, state tables & audit log structure | Pending Specification |
| [**API.md**](./API.md) | REST / WebSocket API specifications connecting frontend UI and agent backend runtime | Pending Specification |
| [**SECURITY.md**](./SECURITY.md) | Sandboxing, filesystem isolation, API key handling & execution safety guarantees | Pending Specification |
| [**UX.md**](./UX.md) | Time Machine UI design system, interaction patterns, timeline visualization & control paradigms | Pending Specification |
| [**DEVELOPMENT_PLAN.md**](./DEVELOPMENT_PLAN.md) | Hackathon timeline (Aug 11-15, 2026), milestone breakdown, critical path & risk mitigation | Pending Specification |
| [**DECISIONS.md**](./DECISIONS.md) | Architecture Decision Records (ADRs) tracking trade-offs and design rationale | Active Log (ADR-001 through ADR-005) |
| [**DEMO.md**](./DEMO.md) | End-to-end hackathon demo script, scenario choreography & judging highlight map | Pending Specification |

---

## Guidelines for Documentation Updates

- All documents should be clear, detailed, and technically rigorous.
- Avoid vagueness or generic boilerplate.
- Every architectural choice must align with the hackathon judging criteria (Technical Execution, UX & Intuition, Creativity, Originality).
