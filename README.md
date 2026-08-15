# REWIND — Ctrl+Z for AI Agents

> **REWIND** is a deterministic safety proxy and transactional execution runtime that gives developers, enterprises, and users a single-click **Ctrl+Z** undo capability for AI agent operations across Filesystems, Git repositories, and PostgreSQL databases.

---

## 🏛️ Core Principles

1. **Untrusted LLM Planner Model**: The LLM is an untrusted proposal engine. It generates structured action proposals (`ActionProposal`) but is **NEVER** allowed to execute tools directly, define tool metadata, or generate rollback logic.
2. **Deterministic State Restoration**: Rollbacks are computed using reverse-topological dependency DAG traversal and executed via pre-image inverse recipes and Git worktrees — **100% independent of the LLM**.
3. **Cross-Domain Verification**: Every post-rollback state assertion verifies actual resulting state across Filesystem, Git, and Database layers, asserting exact SHA-256 Merkle root integrity hash equality (`WorkspaceStateHasher`).
4. **Human-in-the-Loop Approval**: High-risk or irreversible operations require explicit human operator approval before tool execution.

---

## 📐 Architecture & Workflow

```text
┌─────────────────────────┐
│ Next.js 14 Time Machine │
└───────────┬─────────────┘
            │ REST & WebSockets
            ▼
┌─────────────────────────┐
│ FastAPI REST & WS Router│
└───────────┬─────────────┘
            │
            ▼
┌────────────────────────────────┐
│ ControlPlaneRuntimeCoordinator │
└───────┬────────────────┬───────┘
        │                │
┌───────▼─────────────┐ ┌▼────────────────────────┐
│ Untrusted LLM       │ │ Deterministic REWIND   │
│ Planner Proposal    │ │ Interceptor & Policy   │
└─────────────────────┘ └┬───────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌───────────────┐ ┌──────────────┐ ┌──────────────┐
│  Filesystem   │ │ Git Worktree │ │  PostgreSQL  │
│ Sandbox Driver│ │  Driver      │ │  Driver      │
└───────────────┘ └──────────────┘ └──────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                         ▼
             ┌───────────────────────┐
             │ Checkpoint Manager &  │
             │ Merkle Root StateHash │
             └───────────┬───────────┘
                         │
                         ▼
             ┌───────────────────────┐
             │ Reverse Topological   │
             │ Rollback Engine & DAG │
             └───────────────────────┘
```

---

## 🚀 Quickstart Guide

### Prerequisites
* Python 3.12+
* Node.js 18+ / npm 10+
* Docker & Docker Compose (optional for local PostgreSQL instance)

### 1. Repository Setup & Dependencies
```bash
# Clone the repository
git clone https://github.com/rewind-ai/rewind.git
cd rewind

# Install Python backend dependencies
pip install -e agent/ -e backend/
```

### 2. Run Test Suite
```bash
PYTHONPATH=. pytest
```

### 3. Start FastAPI Control Plane API & WebSocket Gateway
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
* **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check**: `GET http://localhost:8000/health`

### 4. Start Next.js Time Machine Visual UI
```bash
cd frontend
npm install
npm run dev
```
* **Time Machine Interface**: [http://localhost:3000](http://localhost:3000)

---

## 🎬 Canonical Hackathon Demo

To run the full 14-stage deterministic hackathon demo scenario (demonstrating multi-step execution, accidental deletion, dependency reversal, and restored-state verification):

```bash
PYTHONPATH=. pytest tests/test_demo_script.py -s
```

---

## 📡 API Sitemap

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/workspaces` | Create jailed workspace |
| `GET` | `/api/v1/workspaces/{id}` | Get workspace details |
| `POST` | `/api/v1/sessions` | Launch agent session |
| `GET` | `/api/v1/sessions/{id}` | Get session status |
| `POST` | `/api/v1/sessions/{id}/pause` | Pause active session |
| `POST` | `/api/v1/sessions/{id}/resume` | Resume session execution |
| `GET` | `/api/v1/sessions/{id}/actions` | List session actions |
| `GET` | `/api/v1/actions/{id}` | Get action details |
| `GET` | `/api/v1/actions/{id}/diff` | Get pre/post state diff |
| `POST` | `/api/v1/actions/{id}/approve` | Approve pending risky action |
| `POST` | `/api/v1/actions/{id}/reject` | Reject pending risky action |
| `GET` | `/api/v1/sessions/{id}/checkpoints` | List session checkpoints |
| `POST` | `/api/v1/rollbacks` | **Trigger Deterministic REWIND** |
| `WS` | `/api/v1/sessions/{session_id}/stream` | Live WebSocket Telemetry & Event Replay |

---

## 📄 License
MIT License. Built for Advanced Agentic Coding.
