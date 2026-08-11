# REWIND Agent Runtime & Interceptor Subsystem

> **Tech Stack**: Python / Abstracted LLM Client / Structured Tool Calling

## Directory Layout (Planned)

```
agent/
├── runtime/          # Agent loop & LLM provider abstraction
├── interceptor/      # Risk evaluator & action interceptor
├── tools/            # Reversible tool definitions (FS, Git, GitHub API, DB)
└── rollback/         # Inverse action generator & DAG builder
```

*Note: Code implementation will begin after specifications in `docs/` are finalized.*
