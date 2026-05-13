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
