# Code Map

Use this file to answer the contributor questions quickly.

## Where does the app start?

- Python package entrypoint: `src/memsmith/api.py`
- CLI entrypoint: `src/memsmith/cli/main.py`
- Server entrypoint: `src/memsmith/server/app.py`

## Where does data flow?

1. `memsmith.session(...)` creates a `Session`.
2. `Session.agent(...)` returns an `AgentContext`.
3. `AgentContext` delegates to `state/` primitives.
4. Persistence and observability sit next to that flow instead of hiding behind service layers.

## Where should I add feature X?

- New agent API method: `src/memsmith/session/agent.py`
- State versioning or waiter logic: `src/memsmith/state/`
- WAL or checkpoint behavior: `src/memsmith/persistence/`
- Watch or dump output: `src/memsmith/observability/` or `src/memsmith/cli/commands/`
- HTTP or WebSocket transport: `src/memsmith/server/`
- LangGraph or CrewAI adapter: `src/memsmith/integrations/`

## How do I run tests?

Run unit tests first. They should stay fast and local.

```bash
pytest tests/unit
pytest tests/integration
pytest tests/smoke
```

## What breaks if I change this?

- `session/manager.py`: almost every public flow
- `session/agent.py`: all user-facing behavior
- `state/`: concurrency and ordering semantics
- `persistence/`: crash recovery guarantees
- `server/`: remote mode only
- `integrations/`: framework-specific entrypoints only
