# REWIND Backend Subsystem

> **Tech Stack**: Python / FastAPI / SQLAlchemy / PostgreSQL

## Directory Layout (Planned)

```
backend/
├── app/
│   ├── api/          # REST & WebSocket endpoints
│   ├── core/         # Configuration, logging & security core
│   ├── db/           # SQLAlchemy models & migrations
│   ├── models/       # Pydantic schemas & DTOs
│   └── services/     # Business logic & rollback execution services
└── tests/            # Backend unit & integration tests
```

*Note: Code implementation will begin after specifications in `docs/` are finalized.*
