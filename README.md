# REWIND — Safety & Reliability Layer for AI Agents

> **Git + Transactions + AI Agent Runtime + Time Machine for Agent Actions**

[![Hackathon](https://img.shields.io/badge/CUTC-Transform_Hackathon_2026-blue)](https://cutc.ca)
[![Status](https://img.shields.io/badge/Status-Initialization_%26_Planning-orange)](#)

---

## Overview

AI agents are rapidly gaining authority to execute multi-step operations across real-world systems (filesystems, git repositories, databases, external APIs). However, when an agent makes a mistake, executes a destructive action, or follows a flawed trajectory, recovery is manual, error-prone, or impossible.

**REWIND** provides a safety and transaction management layer for AI agent runtimes. It enables:
- **Action Provenance & Dependency Tracking**: Every action is logged with context, intention, dependencies, and inverse execution recipes.
- **Transactional State Snapshots & Checkpoints**: Instant environment state capture before and after state-changing operations.
- **Automated Verification & Risk Analysis**: Real-time evaluation of proposed agent steps against safety constraints and invariants.
- **Deterministic & Safe Rollback**: Transactional Ctrl+Z for AI agent operations, reversing multi-step trajectories cleanly.
- **Interactive Time-Machine Interface**: Granular visualization and inspection of agent action history with point-in-time state restoration.

---

## Project Documentation

Detailed project architecture, product specifications, data schemas, and implementation guides live in the [`docs/`](./docs) directory:

- 📋 [**Product Requirement Document (PRD)**](./docs/PRD.md)
- 🏗️ [**System Architecture**](./docs/ARCHITECTURE.md)
- 💾 [**Database & Persistence Schema**](./docs/DATABASE.md)
- 🔌 [**API Specification**](./docs/API.md)
- 🤖 [**Agent Workflow & Tool Specs**](./docs/AGENT_WORKFLOW.md)
- 🛡️ [**Security & Sandboxing Model**](./docs/SECURITY.md)
- 🔄 [**Rollback Engine & Inverses**](./docs/ROLLBACK_ENGINE.md)
- ⚡ [**Execution & State Snapshot Model**](./docs/EXECUTION_MODEL.md)
- 🎨 [**UI/UX & Time Machine Design**](./docs/UX.md)
- 📊 [**Data Model & Event Schemas**](./docs/DATA_MODEL.md)
- 📅 [**Development Plan & Milestones**](./docs/DEVELOPMENT_PLAN.md)
- 🧠 [**Architecture Decision Records (ADRs)**](./docs/DECISIONS.md)
- 🎬 [**Hackathon Demo Plan**](./docs/DEMO.md)

---

## Directory Structure Overview

```
rewind/
├── docs/             # Technical specifications & planning documents
├── frontend/         # Next.js + TypeScript + Tailwind + Framer Motion UI
├── backend/          # FastAPI Python control plane & API services
├── agent/            # Agent runtime, tool calling & rollback engine
├── infra/            # Docker sandboxing & environment orchestration
└── tests/            # End-to-end integration & validation test suites
```

---

## Getting Started

*(Detailed setup instructions will be updated upon completion of the core architectural phase. See [`docs/DEVELOPMENT_PLAN.md`](./docs/DEVELOPMENT_PLAN.md) for current status.)*
