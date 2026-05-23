# MemSmith Backend

This backend uses a boring Python `src` layout on purpose.

The goal is contributor ergonomics, not architecture theater:

- public entrypoints live in `src/memsmith/`
- state engine code lives in `src/memsmith/session/` and `src/memsmith/state/`
- persistence code lives in `src/memsmith/persistence/`
- watch and dump surfaces live in `src/memsmith/observability/` and `src/memsmith/cli/`
- transport code lives in `src/memsmith/server/`
- framework adapters live in `src/memsmith/integrations/`
- tests mirror those boundaries under `tests/`

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python examples/two_agents.py
python examples/crash_recovery.py
python -m memsmith dump two-agent-demo --data-dir .memsmith-examples
python -m memsmith watch two-agent-demo --data-dir .memsmith-examples --limit 1
```

Install the optional server extras when you want the transport demo:

```bash
pip install -e ".[server]"
python examples/server_mode.py
```

Install the optional LiteLLM extra when you want the live multi-model benchmark suite:

```bash
pip install -e ".[llm]"
RUN_LITELLM_MULTIAGENT_SMOKE=1 MEMSMITH_LITELLM_MODELS="groq/llama-3.3-70b-versatile" PYTHONPATH=src ../.venv/bin/python -m pytest tests/Multiagent_test -q -s
```

That suite compares MemSmith coordination against a plain `asyncio` baseline while
capturing watch, dump, checkpoint, WAL, resume, and deterministic output-quality data.
See `docs/llm-benchmark-suite.md` for the full guide.

## Layout

```text
backend/
├── docs/                # contributor docs, architecture notes, code map
├── examples/            # runnable demos and usage snippets
├── src/memsmith/        # installable package
└── tests/               # mirrored test layout
```

## Design Rules

- Keep execution flow grep-friendly.
- Prefer small modules with obvious names over abstraction-heavy layers.
- Add new features next to the boundary that changes with them.
- Avoid generic `utils.py` and `helpers.py` catch-alls.
- Keep the public API centered on `session()` and `session.agent(...)`.

## First Places To Look

- `src/memsmith/api.py`: public package entrypoints
- `src/memsmith/session/manager.py`: session lifecycle and shared state wiring
- `src/memsmith/session/agent.py`: agent-facing API surface
- `src/memsmith/state/`: low-level coordination primitives
- `src/memsmith/persistence/`: WAL, checkpoints, and recovery
- `src/memsmith/observability/`: dump/watch formatting and stream consumers
- `src/memsmith/server/`: FastAPI app and the remote client used by `connect()`
