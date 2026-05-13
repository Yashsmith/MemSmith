# Architecture

MemSmith should stay a modular monolith.

That means one package, one import graph, and a few explicit seams instead of a pile of abstract base classes.

## Boundaries

### `src/memsmith/api.py`

Public constructors live here. New contributors should be able to open one file and answer how a session starts.

### `src/memsmith/session/`

This is the product surface. If the change affects how agents read, wait, lock, checkpoint, or broadcast, start here.

Current flow: `Session` records history, publishes stream envelopes, and coordinates checkpoint/WAL boundaries without hiding those seams behind service layers.

### `src/memsmith/state/`

Low-level coordination primitives. Storage, lock ownership, and wait semantics belong here.

### `src/memsmith/persistence/`

Anything touching WAL, checkpoint files, replay, or on-disk layout belongs here.

Current flow: local pushes append to the file-backed WAL, checkpoints write both binary and JSON artifacts, and resume restores a snapshot before replaying later WAL entries.

### `src/memsmith/observability/`

Anything that powers `memsmith watch`, `memsmith dump`, formatting, or event streaming belongs here.

Current flow: dump output is reconstructed from persisted history artifacts, while watch uses live `StreamEnvelope`s in-process and a WAL-backed consumer across processes.

### `src/memsmith/server/`

Transport only. This layer should adapt HTTP and WebSocket requests into the same session API instead of re-implementing business logic.

Current flow: `server/app.py` owns a session registry, `routes/` adapts HTTP endpoints into the core runtime, and `client.py` wraps that transport back into the same high-level SDK shape.

### `src/memsmith/cli/`

Thin command wrappers. The CLI should orchestrate package APIs, not own business logic.

### `src/memsmith/integrations/`

Adapters for external frameworks. Keep framework-specific code out of the core session implementation.

## Guardrails

- Prefer explicit imports over dynamic loading.
- Prefer composition over inheritance.
- Keep module names concrete and grep-friendly.
- Do not add generic `utils.py` unless the abstraction is proven.
- When in doubt, add code next to the boundary that changes with it.

## Contributor Path

1. Start from `src/memsmith/api.py` to see which public constructor owns the behavior.
2. Step into `session/manager.py` or `session/agent.py` for the deciding runtime path.
3. Move outward into `state/`, `persistence/`, `observability/`, or `server/` only when that boundary actually owns the behavior you are changing.
