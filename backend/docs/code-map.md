# Code Map

Use this file to answer the contributor questions quickly.

## Where does the app start?

- Python package entrypoint: `src/memsmith/api.py`
- Module entrypoint: `src/memsmith/__main__.py`
- CLI entrypoint: `src/memsmith/cli/main.py`
- Server entrypoint: `src/memsmith/server/app.py`

## Where does data flow?

1. `memsmith.session(...)` creates a `Session`.
2. `Session.agent(...)` returns an `AgentContext`.
3. `AgentContext` delegates to `state/` primitives.
4. `session/manager.py` records history, appends WAL entries, and publishes watch envelopes.
5. Persistence and observability sit next to that flow instead of hiding behind service layers.
6. `memsmith.connect(...)` returns `server/client.py`, which talks to the FastAPI app while keeping the same high-level session shape.

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
python -m compileall src tests examples
```

Run the live LLM benchmark suite only when you want provider-backed coverage of the
MemSmith coordination and explainability surface:

```bash
RUN_LITELLM_MULTIAGENT_SMOKE=1 MEMSMITH_LITELLM_MODELS="groq/llama-3.3-70b-versatile" PYTHONPATH=src ../.venv/bin/python -m pytest tests/Multiagent_test -q -s
```

## What commands actually work today?

```bash
python examples/two_agents.py
python examples/crash_recovery.py
python -m memsmith dump two-agent-demo --data-dir .memsmith-examples
python -m memsmith watch two-agent-demo --data-dir .memsmith-examples --limit 1
python examples/server_mode.py
```

The live benchmark suite entrypoint lives in `tests/Multiagent_test/` and uses LiteLLM
to compare MemSmith coordination against a manual baseline while saving watch, dump,
checkpoint, WAL, resume, transcript, and quality-report artifacts.

## What breaks if I change this?

- `session/manager.py`: almost every public flow
- `session/agent.py`: all user-facing behavior
- `state/`: concurrency and ordering semantics
- `persistence/`: crash recovery guarantees
- `server/`: remote mode only
- `integrations/`: framework-specific entrypoints only
