# Agent Workflow Specification — REWIND

> **Status**: Draft / Pending Detailed Specification  

---

## 1. Overview

Defines how the agent interacts with LLM providers, structures tool calls, handles risk interception, and registers inverse operations.

---

## 2. Key Components

- **LLM Abstraction Layer**: Pluggable support for OpenAI, Anthropic, Gemini, or local models via standard tool-calling interface.
- **Tool Interceptor Lifecycle**:
  1. LLM proposes tool execution.
  2. Interceptor checks action risk rating.
  3. Pre-execution snapshot captured.
  4. Tool executed within sandbox.
  5. Inverse recipe synthesized and logged alongside outcome.
  6. Post-execution state snapshot recorded.
- **Verification Loop**: Execution of automated checks (e.g. `npm test`, linter, syntax validation) after action completion.
