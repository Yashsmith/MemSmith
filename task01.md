# Title

Implement MemSmith v3 from the current scaffold to a usable local-first release candidate.

# Goal

Turn the existing backend scaffold into a working MemSmith implementation that satisfies the v3 PRD's primary promise: an in-process Python SDK for shared multi-agent state with version-aware waiting, lock semantics, crash recovery, human-readable history export, optional server mode, and contributor-friendly docs/tests.

# User outcome

After this plan is executed, a contributor or end user should be able to:

- install MemSmith from the backend package with one command
- run a two-agent local example end to end
- use `push`, `get`, `wait_for`, `lock`, `broadcast`, `checkpoint`, and `resume` with real semantics
- inspect history through `memsmith dump`
- observe live session activity through `memsmith watch`
- optionally start a local server and connect another process to the same session
- understand where to extend the system without rediscovering the codebase

# Project context

- MemSmith is the SQLite of multi-agent state: local-first, SDK-first, zero-infra by default.
- The repo should remain a boring modular monolith with explicit seams.
- The primary product surface is the Python SDK under `backend/src/memsmith/`.
- The main change boundaries in the current repo are:
  - `backend/src/memsmith/api.py`
  - `backend/src/memsmith/session/`
  - `backend/src/memsmith/state/`
  - `backend/src/memsmith/persistence/`
  - `backend/src/memsmith/observability/`
  - `backend/src/memsmith/server/`
  - `backend/src/memsmith/cli/`
  - `backend/src/memsmith/integrations/`
  - `backend/tests/`
  - `backend/examples/`
  - `backend/docs/`
- The PRD is the product anchor. The backend docs are the architecture anchor.

# Current repo state

- Repo root contains `PRD.md` and an initialized `backend/` package.
- No existing root task files were present during planning; this file is `task01.md`.
- The backend scaffold compiles and the current `examples/two_agents.py` runs.
- The current code already supports a local happy path for `session()`, `push()`, `get()`, `wait_for()`, `lock()`, `history()`, `checkpoint()`, and `export()`, but most advanced behavior is still stubbed or incomplete.
- `backend/docs/architecture.md` and `backend/docs/code-map.md` reflect the current modular-monolith direction.
- `PRD.md` still describes an older internal file tree under `memsmith/core/`, while the actual repo uses `backend/src/memsmith/session|state|persistence|observability|server|cli|integrations`.

## Progress

- 2026-05-13: Planning document created from `PRD.md`, the backend scaffold, examples, and tests. No implementation work has started.
- 2026-05-13 20:59:00 IST: Completed Step 1. Added timestamped history events, explicit session transport/runtime metadata, and separate state-key vs lock-key helpers while preserving the current local SDK happy path.
- 2026-05-13 21:01:33 IST: Completed Step 2. Replaced the single-dict store with a real multi-shard store, moved writes onto shard-scoped async locks, and added snapshot coverage plus state-semantics integration tests.
- 2026-05-13 21:03:41 IST: Completed Step 3. Finalized the session-scoped lock-key boundary, added lock wait/reentry semantics, and verified the existing version-aware wait path with focused tests.
- 2026-05-13 21:06:01 IST: Completed Step 4. Added a file-backed WAL with msgspec msgpack frames, a background flush thread, explicit flush/close lifecycle hooks, and verified that local pushes now create durable WAL artifacts on disk.
- 2026-05-13 21:09:32 IST: Completed Step 5. Added checkpoint snapshot serialization plus JSON sidecars, store restore helpers, real `resume()` recovery with WAL replay after the latest checkpoint, and verified restored state through integration and smoke paths.
- 2026-05-13 21:13:35 IST: Completed Step 6. Added timestamp-aware dump formatting, JSON history serialization with rendered lines, and a real `memsmith dump` CLI that reads persisted session history from WAL/checkpoint artifacts.
- 2026-05-13 21:17:54 IST: Completed Step 7. Added runtime stream envelopes, a persisted WAL watch consumer, a minimal `memsmith watch` CLI, and a package `__main__` entrypoint so `python -m memsmith watch ...` works.
- 2026-05-13 21:27:31 IST: Completed Step 8. Replaced the server route stubs with a real FastAPI app and session registry, added a thin remote HTTP client for `memsmith.connect()`, and verified end-to-end remote push/get/wait behavior plus the server example.
- 2026-05-13 21:28:40 IST: Completed Step 9. Replaced the placeholder integration seams with thin session-backed adapters for LangGraph, CrewAI, and the optional OpenAI Agents store, and verified they delegate into the same checkpoint-aware core runtime.
- 2026-05-13 21:32:09 IST: Completed Step 10. Synced the PRD/backend docs to the implemented repo layout and working commands, made the examples accept overridable data directories for isolated smoke runs, and verified the contributor path plus example suite against the real code.

# Scope

This plan covers the current MemSmith v3 roadmap as it maps to the actual repo:

- hardening the local SDK contract
- implementing real sharded in-memory state semantics
- implementing version-aware waiting and session-scoped locking
- implementing file-backed WAL, checkpoints, and recovery
- implementing human-readable dump and live watch observability flows
- implementing optional FastAPI-based server mode and remote client parity
- implementing minimal framework adapters for LangGraph and CrewAI
- updating docs, examples, and tests so contributors can verify behavior quickly

# Non-goals

- Redis replacement benchmarking or production-scale clustering
- distributed consensus, multi-node replication, or quorum protocols
- PostgreSQL, SQLite-as-storage-engine, Neo4j, or other external database integrations
- frontend web UI development
- managed cloud features, auth, billing, tenancy, or hosted control plane work
- aggressive micro-optimization or benchmark gating in default CI
- building broad abstraction layers that are not yet required by the codebase

# Assumptions

- Python `3.11+` remains the minimum supported version.
- `backend/pyproject.toml` remains the single packaging/configuration source.
- In-process SDK mode remains the source of truth; server mode adapts the same contract.
- Tests remain split into `backend/tests/unit`, `backend/tests/integration`, and `backend/tests/smoke`.
- The current scaffold may be extended, but large parallel implementations should be avoided.
- Hot-path performance checks for concurrency, WAL, and recovery should be targeted and mostly local/manual rather than blocking default CI.

# Relevant files

- `[Exists]` `PRD.md`
- `[Exists]` `backend/pyproject.toml`
- `[Exists]` `backend/README.md`
- `[Exists]` `backend/docs/architecture.md`
- `[Exists]` `backend/docs/code-map.md`
- `[Exists]` `backend/docs/contributing.md`
- `[Exists]` `backend/src/memsmith/api.py`
- `[Exists]` `backend/src/memsmith/errors.py`
- `[Exists]` `backend/src/memsmith/types.py`
- `[Exists]` `backend/src/memsmith/session/manager.py`
- `[Exists]` `backend/src/memsmith/session/agent.py`
- `[Exists]` `backend/src/memsmith/state/shard_store.py`
- `[Exists]` `backend/src/memsmith/state/locks.py`
- `[Exists]` `backend/src/memsmith/state/waiters.py`
- `[Exists]` `backend/src/memsmith/persistence/paths.py`
- `[Exists]` `backend/src/memsmith/persistence/wal.py`
- `[Exists]` `backend/src/memsmith/persistence/checkpoint.py`
- `[Exists]` `backend/src/memsmith/persistence/recovery.py`
- `[Exists]` `backend/src/memsmith/observability/history.py`
- `[Exists]` `backend/src/memsmith/observability/streams.py`
- `[Exists]` `backend/src/memsmith/server/app.py`
- `[Exists]` `backend/src/memsmith/server/routes/health.py`
- `[Exists]` `backend/src/memsmith/server/routes/sessions.py`
- `[Exists]` `backend/src/memsmith/server/routes/streams.py`
- `[Exists]` `backend/src/memsmith/server/ws.py`
- `[Exists]` `backend/src/memsmith/cli/main.py`
- `[Exists]` `backend/src/memsmith/cli/commands/dump.py`
- `[Exists]` `backend/src/memsmith/cli/commands/watch.py`
- `[Exists]` `backend/src/memsmith/cli/commands/serve.py`
- `[Exists]` `backend/src/memsmith/integrations/langgraph.py`
- `[Exists]` `backend/src/memsmith/integrations/crewai.py`
- `[Exists]` `backend/src/memsmith/integrations/openai_agents.py`
- `[Exists]` `backend/examples/two_agents.py`
- `[Exists]` `backend/examples/server_mode.py`
- `[Exists]` `backend/examples/crash_recovery.py`
- `[Exists]` `backend/tests/unit/test_public_api.py`
- `[Exists]` `backend/tests/unit/test_session_flow.py`
- `[Exists]` `backend/tests/integration/test_layout.py`
- `[Exists]` `backend/tests/smoke/test_examples.py`
- `[Create]` `backend/src/memsmith/observability/watch.py`
- `[Create]` `backend/src/memsmith/server/client.py`
- `[Create]` `backend/tests/unit/test_shard_store.py`
- `[Create]` `backend/tests/unit/test_locks.py`
- `[Create]` `backend/tests/unit/test_waiters.py`
- `[Create]` `backend/tests/unit/test_history_format.py`
- `[Create]` `backend/tests/unit/test_wal.py`
- `[Create]` `backend/tests/integration/test_persistence_recovery.py`
- `[Create]` `backend/tests/integration/test_server_transport.py`
- `[Create]` `backend/tests/integration/test_cli_dump.py`
- `[Create]` `backend/tests/smoke/test_server_mode.py`

# File-by-file / function-by-function audit

- `backend/src/memsmith/api.py` — `Exists`
  - `session(name, data_dir=None) -> Session`: returns a local `Session`; no directory creation or persistence bootstrapping.
  - `connect(name, host) -> Session`: async stub that returns a local `Session` with `remote_host` set; no network client or transport logic.
  - `resume(name, data_dir=None) -> Session`: async stub that returns a `Session` with `recovered=True`; no checkpoint load or WAL replay.

- `backend/src/memsmith/session/manager.py` — `Exists`
  - `Session.agent(agent_name) -> AgentContext`: current local entrypoint for agent handles.
  - `Session.full_key(agent_name, key)`: builds state keys as `agent:key`.
  - `Session.preview(value)`: truncates `repr(value)` for history previews.
  - `Session.record_event(...)`: appends `HistoryEvent` entries, but current events have no timestamps.
  - `Session.notify(key)`: wakes waiters through `WaitRegistry`.
  - `Session.broadcast(...)`: records a broadcast event only; no fan-out behavior beyond history.
  - `Session.history()`: returns in-memory history only.
  - `Session.checkpoint(label)`: records a checkpoint event only; no file I/O.
  - `Session.export(path)`: writes JSON history export to a requested path.

- `backend/src/memsmith/session/agent.py` — `Exists`
  - `AgentContext.push(key, value)`: stores a new value in memory, records a `PUSH`, notifies waiters; no WAL append.
  - `AgentContext.get(key)`: reads the current agent's key only and records `GET`.
  - `AgentContext.wait_for(source_agent, key, after_version=None, timeout_ms=30000)`: version-aware wait against in-memory state using `asyncio.Condition`; returns current value immediately if already present.
  - `AgentContext.lock(key, timeout_ms=5000)`: wraps `LockRegistry.acquire` / `release` and records lock events.
  - `AgentContext.try_lock(key)`: returns current lock status only.
  - Important current mismatch: lock keys are built with `Session.full_key(self.name, key)`, so two different agents do not contend for the same logical key. This conflicts with the PRD's cross-agent lock examples.

- `backend/src/memsmith/state/shard_store.py` — `Exists`
  - `ShardStore.get(key)`: returns the latest `StateValue`.
  - `ShardStore.version(key)`: returns the latest integer version or `0`.
  - `ShardStore.set(key, value)`: increments version and stores a `StateValue`.
  - Important current mismatch: the file is named `shard_store.py`, but the implementation is a single dictionary without actual sharding or per-shard locking.

- `backend/src/memsmith/state/locks.py` — `Exists`
  - `LockRegistry._lock(key)`: creates per-key `asyncio.Lock` objects lazily.
  - `LockRegistry.acquire(key, owner, timeout_ms)`: acquires a per-key lock and records the owner.
  - `LockRegistry.release(key, owner)`: releases only if the current owner matches.
  - `LockRegistry.status(key)`: returns `LockInfo`.
  - Important current mismatch: same-owner reacquisition is not reentrant; it will wait on the same `asyncio.Lock` instead of returning the current ownership state.

- `backend/src/memsmith/state/waiters.py` — `Exists`
  - `WaitRegistry.for_key(key)`: caches `asyncio.Condition` per state key.
  - Current logic is suitable for in-loop waiting, but it is not wired to any persistence or cross-process notifications.

- `backend/src/memsmith/persistence/paths.py` — `Exists`
  - `session_home(session_name, base_dir=None)`: returns `.memsmith/<session_name>` by default.

- `backend/src/memsmith/persistence/wal.py` — `Exists`
  - `WALEntry`: structured in-memory log entry.
  - `WAL.append(...)`: appends to an in-memory list only.
  - Important current mismatch: no thread-safe queue, no file-backed append log, no msgspec encoding, no flush lifecycle.

- `backend/src/memsmith/persistence/checkpoint.py` — `Exists`
  - `CheckpointWriter.path_for(label)`: resolves a checkpoint path only.
  - No snapshot writing or reading yet.

- `backend/src/memsmith/persistence/recovery.py` — `Exists`
  - `RecoveryPlan`: dataclass only.
  - No recovery planner or replay logic exists yet.

- `backend/src/memsmith/observability/history.py` — `Exists`
  - `format_event(event)`: produces a simple single-line string, but not the richer timestamped dump format described in the PRD.

- `backend/src/memsmith/observability/streams.py` — `Exists`
  - `StreamEnvelope`: stable event wrapper for future local/remote watch streams.
  - Not currently emitted by the session flow.

- `backend/src/memsmith/server/app.py` — `Exists`
  - `create_app() -> dict[str, object]`: returns a route description dictionary, not a FastAPI app.

- `backend/src/memsmith/server/routes/health.py` — `Exists`
  - `health_routes()`: describes `GET /health` and `GET /ready`.

- `backend/src/memsmith/server/routes/sessions.py` — `Exists`
  - `session_routes()`: describes push/get/broadcast routes as tuples only.

- `backend/src/memsmith/server/routes/streams.py` — `Exists`
  - `stream_routes()`: describes history and watch stream routes as tuples only.

- `backend/src/memsmith/server/ws.py` — `Exists`
  - `watch_channel_name(session_name)`: builds a stream name string only.

- `backend/src/memsmith/cli/main.py` — `Exists`
  - `build_parser()`: registers `dump`, `serve`, and `watch` subcommands.
  - `main(argv=None)`: dispatches to command handlers.

- `backend/src/memsmith/cli/commands/dump.py` — `Exists`
  - `run(args)`: prints scaffold text only.

- `backend/src/memsmith/cli/commands/watch.py` — `Exists`
  - `run(args)`: prints scaffold text only.

- `backend/src/memsmith/cli/commands/serve.py` — `Exists`
  - `run(args)`: prints scaffold text only.

- `backend/src/memsmith/integrations/langgraph.py` — `Exists`
  - `MemSmithCheckpointer`: placeholder dataclass only.

- `backend/src/memsmith/integrations/crewai.py` — `Exists`
  - `MemSmithMemory`: placeholder dataclass only.

- `backend/src/memsmith/integrations/openai_agents.py` — `Exists`
  - `MemSmithStore`: placeholder dataclass only.

- `backend/examples/two_agents.py` — `Exists`
  - Demonstrates the current in-memory happy path and already passes.

- `backend/examples/server_mode.py` — `Exists`
  - Calls `memsmith.connect(...)`, but this currently returns a local `Session`; no real server involvement exists.

- `backend/examples/crash_recovery.py` — `Exists`
  - Returns `recovered=True` from `resume()`, but no state is actually reloaded.

- `backend/tests/unit/test_public_api.py` — `Exists`
  - Verifies top-level constructors and version export.

- `backend/tests/unit/test_session_flow.py` — `Exists`
  - Verifies local `push` + `wait_for` and lock history ordering.

- `backend/tests/integration/test_layout.py` — `Exists`
  - Verifies docs/examples/server scaffold files exist.

- `backend/tests/smoke/test_examples.py` — `Exists`
  - Verifies the two-agent example returns expected data.

# Current behavior

Current working behavior:

- local in-process session creation works
- local `push`, `get`, `wait_for`, and `lock` semantics work for the current happy path
- in-memory event history works
- JSON export of current in-memory history works
- CLI parsing works
- package and examples compile and the two-agent example passes

Current non-working or placeholder behavior:

- no actual sharded store implementation
- no per-shard locks in the store
- no file-backed WAL
- no actual checkpoint file writing
- no actual resume/recovery logic
- no timestamped dump format
- no watch stream or TUI
- no actual FastAPI server
- no remote client transport
- no real framework integrations
- cross-agent lock contention semantics do not match the PRD examples

# Backend dataflow

Current dataflow:

1. `memsmith.session(name)` in `backend/src/memsmith/api.py` returns `Session`.
2. `Session.agent(agent_name)` in `backend/src/memsmith/session/manager.py` returns `AgentContext`.
3. `AgentContext.push(key, value)` in `backend/src/memsmith/session/agent.py` builds `agent:key`, calls `ShardStore.set`, records a `PUSH`, and calls `Session.notify`.
4. `AgentContext.wait_for(source_agent, key, ...)` checks current store state, otherwise waits on `WaitRegistry.for_key(full_key)` until `ShardStore.version(full_key)` advances.
5. `AgentContext.lock(key, ...)` calls `LockRegistry.acquire`, yields control, then calls `LockRegistry.release`.
6. `Session.history`, `Session.export`, `Session.checkpoint`, and `Session.broadcast` operate only on in-memory history today.

Target backend dataflow after implementation:

1. Public SDK entrypoint constructs a real local session runtime with state, persistence, and observability wiring.
2. `AgentContext` mutates a real sharded in-memory store guarded by per-shard locks.
3. Mutations append to a file-backed WAL via a background flush thread and emit stream envelopes for observability.
4. `wait_for` resolves against state versions and local/remote notifications without polling.
5. `checkpoint()` snapshots the current state to disk and writes a human-readable export.
6. `resume()` loads checkpoint state, replays newer WAL entries, and returns a recovered session.
7. CLI and server mode both call into the same session/persistence/observability logic rather than re-implementing business rules.

# Public API / CLI surfaces

Current public SDK surfaces:

- `memsmith.session(name, data_dir=None)`
- `await memsmith.connect(name, host=...)`
- `await memsmith.resume(name, data_dir=None)`
- `session.agent(name).push(key, value)`
- `session.agent(name).get(key)`
- `session.agent(name).wait_for(source_agent, key, after_version=None, timeout_ms=30000)`
- `session.agent(name).lock(key, timeout_ms=5000)`
- `await session.agent(name).try_lock(key)`
- `await session.broadcast(event, payload=None)`
- `await session.history()`
- `await session.checkpoint(label)`
- `await session.export(path)`

Current CLI surfaces:

- `memsmith dump <session>`
- `memsmith watch <session>`
- `memsmith serve --host 127.0.0.1 --port 7117`

Required implementation outcome:

- Keep the current public API names.
- Tighten semantics so SDK behavior matches the PRD without adding a second public path.
- Keep CLI commands as thin wrappers over package logic.

# Persistence / storage impact

- No SQL database is present or planned for this implementation.
- Local on-disk storage under `.memsmith/<session>/` is the persistence model.
- Persistence work should be concentrated in `backend/src/memsmith/persistence/` and wired through `Session`.
- Required outputs:
  - append-only WAL file
  - checkpoint file(s)
  - optional JSON sidecar or export artifact for human-readable debugging
- Recovery should load checkpoint state first, then replay WAL entries newer than the checkpoint.

# Server / transport impact

- Current server mode is route metadata only.
- Real transport work should stay in `backend/src/memsmith/server/`.
- The actual endpoints implied by the current route files are:
  - `GET /health`
  - `GET /ready`
  - `POST /sessions/{session}/agents/{agent}/state/{key}`
  - `GET /sessions/{session}/agents/{agent}/state/{key}`
  - `POST /sessions/{session}/broadcast/{event}`
  - `GET /sessions/{session}/history`
  - `WS /sessions/{session}/watch`
- `memsmith.connect()` needs a real remote client implementation that preserves the same session/agent contract.

# Observability impact

- Current history exists only in memory and lacks timestamps.
- `format_event()` exists, but it does not yet match the PRD's dump timeline format.
- `StreamEnvelope` exists but is not emitted by the session flow.
- `memsmith dump` and `memsmith watch` currently print placeholder strings.
- Observability work should add:
  - timestamped `HistoryEvent` records
  - local event streaming from the session runtime
  - human-readable dump output matching the PRD
  - a watch UI launch path that does not hide business logic in the CLI layer

# Integration impact

- LangGraph, CrewAI, and OpenAI Agents adapter files exist only as placeholders.
- The PRD's committed P2 integrations are LangGraph and CrewAI; OpenAI Agents is present in the repo but not required to unblock the first useful local release.
- Integration adapters should remain thin wrappers over the stable core session/checkpoint APIs.

# Frontend impact

Not present in current codebase.

# Database impact

Not present in current codebase.

# Neo4j impact

Not present in current codebase.

# Reuse opportunities

- Reuse the existing `Session` and `AgentContext` as the public local runtime instead of replacing them.
- Reuse `WaitRegistry` as the place where version-aware wait coordination lives.
- Reuse `LockRegistry` but change the keying contract so locks can contend across agents when required.
- Reuse `session_home()` for all persistence paths.
- Reuse `HistoryEvent`, `StateValue`, and `LockInfo` as the stable data-model surface, extending them only where needed.
- Reuse the existing CLI parser and route-description files as the command and transport contract anchors.
- Reuse the current tests and examples as smoke coverage while expanding deeper unit and integration coverage.
- Reuse the modular structure in `backend/docs/architecture.md` and `backend/docs/code-map.md` instead of introducing new layers.

# Phase breakdown

## Phase 1 — Core SDK and state semantics

- Step 1: Harden the public SDK, history model, and session contract.
- Step 2: Implement a real sharded store with per-shard locking and snapshot support.
- Step 3: Finalize version-aware waiting and session-scoped lock semantics.

## Phase 2 — Reliability and recovery

- Step 4: Implement filesystem-backed WAL infrastructure and lifecycle.
- Step 5: Implement checkpoint writing, resume, and WAL replay.

## Phase 3 — Observability and transport

- Step 6: Implement structured history export and `memsmith dump`.
- Step 7: Implement local watch streaming and the `memsmith watch` TUI path.
- Step 8: Implement FastAPI server mode and remote client parity.

## Phase 4 — Integrations, docs, and OSS polish

- Step 9: Implement thin LangGraph and CrewAI adapter surfaces.
- Step 10: Sync examples, docs, PRD-facing architecture notes, and contributor flows.

# Implementation plan broken into small steps

## Step 1 — Harden the SDK contract and event model

Why this exists:

- The public API already exists, but some semantics are placeholders or internally inconsistent with the PRD.

Files to change:

- `backend/src/memsmith/api.py`
- `backend/src/memsmith/session/manager.py`
- `backend/src/memsmith/session/agent.py`
- `backend/src/memsmith/types.py`
- `backend/src/memsmith/errors.py`
- `backend/tests/unit/test_public_api.py`
- `backend/tests/unit/test_session_flow.py`
- `backend/examples/two_agents.py`

What will change:

- Add timestamp support to history events.
- Tighten `Session` lifecycle/state fields needed for later persistence and observability.
- Make the current SDK semantics explicit where the PRD depends on them.
- Prepare helper boundaries for state keys versus lock keys.

What existing code should be reused:

- `Session`, `AgentContext`, `HistoryEvent`, and existing unit tests.

What will be verified:

- top-level public API still imports cleanly
- local two-agent flow still passes
- history/export data model includes the fields needed for dump/watch work

Which commands prove it passed:

- `cd backend && python -m pytest tests/unit/test_public_api.py tests/unit/test_session_flow.py`
- `cd backend && python examples/two_agents.py`

## Step 2 — Implement the real sharded store

Why this exists:

- The current store is a single dict. The repo and PRD already name a sharded store, so the implementation needs to match the design.

Files to change:

- `backend/src/memsmith/state/shard_store.py`
- `backend/src/memsmith/session/manager.py`
- `backend/src/memsmith/session/agent.py`
- `backend/src/memsmith/types.py`
- `[Create] backend/tests/unit/test_shard_store.py`
- `[Create] backend/tests/integration/test_state_semantics.py`

What will change:

- Replace the single `_values` dict with actual shards.
- Add per-shard `asyncio.Lock` usage inside the store.
- Add snapshot/read APIs needed by checkpoints and dump/export.

What existing code should be reused:

- current `StateValue` model
- current `ShardStore.version()` contract

What will be verified:

- versions increment correctly
- writes to different keys can proceed without corrupting shared state
- snapshot iteration returns consistent state for checkpoint/export use

Which commands prove it passed:

- `cd backend && python -m pytest tests/unit/test_shard_store.py tests/integration/test_state_semantics.py`

## Step 3 — Finalize wait and lock semantics

Why this exists:

- `wait_for()` is one of the core product promises, and current lock behavior does not match the PRD's cross-agent examples.

Files to change:

- `backend/src/memsmith/state/waiters.py`
- `backend/src/memsmith/state/locks.py`
- `backend/src/memsmith/session/agent.py`
- `backend/src/memsmith/session/manager.py`
- `[Create] backend/tests/unit/test_waiters.py`
- `[Create] backend/tests/unit/test_locks.py`
- `backend/tests/unit/test_session_flow.py`

What will change:

- Keep version-aware wait semantics explicit and regression-tested.
- Separate lock keys from agent-scoped state keys so multiple agents can contend on the same logical lock target.
- Make timeout and lock-conflict behavior stable and visible.

What existing code should be reused:

- `WaitRegistry.for_key()`
- `LockRegistry.status()`
- `MemSmithTimeoutError` and `LockConflictError`

What will be verified:

- immediate wait resolution when the value already exists
- timeout behavior when the value never arrives
- cross-agent lock conflict on the same logical key
- lock release after context exit, including exception exit path

Which commands prove it passed:

- `cd backend && python -m pytest tests/unit/test_waiters.py tests/unit/test_locks.py tests/unit/test_session_flow.py`

## Step 4 — Implement filesystem-backed WAL

Why this exists:

- The current WAL is in-memory only, so crash recovery cannot work.

Files to change:

- `backend/src/memsmith/persistence/paths.py`
- `backend/src/memsmith/persistence/wal.py`
- `backend/src/memsmith/session/manager.py`
- `backend/src/memsmith/session/agent.py`
- `backend/pyproject.toml`
- `[Create] backend/tests/unit/test_wal.py`
- `[Create] backend/tests/integration/test_wal_flow.py`

What will change:

- Add msgspec-backed WAL entry encoding/decoding.
- Add a thread-safe queue and background flush worker.
- Create session persistence directories on demand.
- Wire `push`/broadcast/checkpoint events into WAL append behavior where appropriate.

What existing code should be reused:

- `session_home()`
- current `WALEntry` concept and `WAL.append()` call site shape

What will be verified:

- WAL files are created under the session home
- appended entries round-trip correctly
- writes are flushed in order
- local push paths now leave durable WAL artifacts

Which commands prove it passed:

- `cd backend && python -m pytest tests/unit/test_wal.py tests/integration/test_wal_flow.py`

## Step 5 — Implement checkpoints and resume/recovery

Why this exists:

- The PRD's crash-recovery promise depends on actual snapshot writing and replay.

Files to change:

- `backend/src/memsmith/persistence/checkpoint.py`
- `backend/src/memsmith/persistence/recovery.py`
- `backend/src/memsmith/session/manager.py`
- `backend/src/memsmith/api.py`
- `backend/src/memsmith/state/shard_store.py`
- `backend/examples/crash_recovery.py`
- `[Create] backend/tests/integration/test_persistence_recovery.py`
- `backend/tests/smoke/test_examples.py`

What will change:

- Write binary checkpoint snapshots plus a readable JSON sidecar or equivalent debug artifact.
- Build a recovery plan that loads checkpoint state and replays later WAL entries.
- Make `resume()` perform real recovery work rather than just setting a boolean flag.

What existing code should be reused:

- `CheckpointWriter.path_for()`
- `RecoveryPlan`
- current crash recovery example as the smoke path

What will be verified:

- checkpoint files exist after `checkpoint()`
- recovered sessions actually contain stored state
- the crash recovery example validates real persistence instead of a stubbed flag

Which commands prove it passed:

- `cd backend && python -m pytest tests/integration/test_persistence_recovery.py tests/smoke/test_examples.py`
- `cd backend && python examples/crash_recovery.py`

## Step 6 — Implement structured history export and `memsmith dump`

Why this exists:

- Human-readable debugging is a core product differentiator in the PRD.

Files to change:

- `backend/src/memsmith/types.py`
- `backend/src/memsmith/observability/history.py`
- `backend/src/memsmith/session/manager.py`
- `backend/src/memsmith/cli/commands/dump.py`
- `[Create] backend/tests/unit/test_history_format.py`
- `[Create] backend/tests/integration/test_cli_dump.py`

What will change:

- Add timestamp-aware event rendering that matches the PRD dump style.
- Make `dump` read/export actual session history or persisted session data.
- Keep CLI logic thin by delegating rendering to observability helpers.

What existing code should be reused:

- `format_event()`
- `Session.export()`
- CLI parser registration in `cli/main.py`

What will be verified:

- dump formatting is stable and testable
- dump command prints expected timeline content
- exported JSON remains machine-readable and human-readable enough for debugging

Which commands prove it passed:

- `cd backend && python -m pytest tests/unit/test_history_format.py tests/integration/test_cli_dump.py`

## Step 7 — Implement local watch streaming and the TUI path

Why this exists:

- `memsmith watch` is the PRD's killer feature and must be built on real session events.

Files to change:

- `backend/src/memsmith/observability/streams.py`
- `[Create] backend/src/memsmith/observability/watch.py`
- `backend/src/memsmith/session/manager.py`
- `backend/src/memsmith/cli/commands/watch.py`
- `backend/pyproject.toml`
- `[Create] backend/tests/integration/test_watch_stream.py`

What will change:

- Emit `StreamEnvelope` instances from the session runtime.
- Add a local watch consumer model for live event streaming.
- Launch a minimal Rich/Textual-driven watch experience from the CLI command.

What existing code should be reused:

- `StreamEnvelope`
- current session event recording flow
- existing `watch` command registration

What will be verified:

- event stream ordering for push/lock/broadcast flows
- watch command receives and renders live updates without blocking the session path
- local watch behavior is at least smoke-testable at the stream layer even if the full TUI remains partly manual

Which commands prove it passed:

- `cd backend && python -m pytest tests/integration/test_watch_stream.py`
- `cd backend && python -m memsmith watch two-agent-demo`  
  Manual verification: live events appear in the terminal for a running example session.

Implementation note after execution:

- `backend/pyproject.toml` already had the optional `watch` dependencies, so no package-metadata change was needed.
- `backend/src/memsmith/__main__.py` had to be added so the planned `python -m memsmith watch ...` command actually executes the CLI.

## Step 8 — Implement FastAPI server mode and remote client parity

Why this exists:

- The PRD's secondary mode requires multi-process access to the same session semantics.

Files to change:

- `backend/src/memsmith/server/app.py`
- `backend/src/memsmith/server/__init__.py`
- `backend/src/memsmith/server/schemas.py`
- `backend/src/memsmith/server/routes/health.py`
- `backend/src/memsmith/server/routes/sessions.py`
- `backend/src/memsmith/server/routes/streams.py`
- `backend/src/memsmith/server/ws.py`
- `[Create] backend/src/memsmith/server/client.py`
- `backend/src/memsmith/api.py`
- `backend/examples/server_mode.py`
- `[Create] backend/tests/integration/test_server_transport.py`
- `[Create] backend/tests/smoke/test_server_mode.py`

What will change:

- Replace route-description dictionaries with a real FastAPI app.
- Add a session registry for server-mode runtimes.
- Add history and watch endpoints backed by the same core logic.
- Implement a remote client/session adapter used by `memsmith.connect()`.

What existing code should be reused:

- existing route shapes in `server/routes/*.py`
- core `Session` and `AgentContext` behavior as the source of truth

What will be verified:

- health and readiness endpoints respond
- remote client can push/get/wait against a running server
- server-mode example uses actual transport instead of a stub

Which commands prove it passed:

- `cd backend && python -m pytest tests/integration/test_server_transport.py tests/smoke/test_server_mode.py`
- `cd backend && python examples/server_mode.py`

Implementation note after execution:

- `backend/pyproject.toml` already declared the optional `server` dependencies, so the step only needed environment installation, not package metadata changes.
- `backend/src/memsmith/server/__init__.py` had to become lazy so importing `memsmith` does not eagerly require FastAPI when server extras are not installed.

## Step 9 — Implement thin LangGraph and CrewAI adapters

Why this exists:

- The PRD's Phase 4 integration story depends on thin wrappers around the stable core session and persistence paths.

Files to change:

- `backend/src/memsmith/integrations/langgraph.py`
- `backend/src/memsmith/integrations/crewai.py`
- `backend/src/memsmith/integrations/openai_agents.py`
- `[Create] backend/tests/integration/test_integrations.py`

What will change:

- Replace placeholder dataclasses with thin adapters that delegate to MemSmith session/checkpoint behavior.
- Keep OpenAI Agents support optional if it does not block the LangGraph and CrewAI commitments.

What existing code should be reused:

- core SDK methods from `api.py`, `session/manager.py`, and `session/agent.py`

What will be verified:

- adapters can be instantiated and call through to MemSmith core behaviors
- adapter tests demonstrate the integration seam without re-implementing business logic

Which commands prove it passed:

- `cd backend && python -m pytest tests/integration/test_integrations.py`

Implementation note after execution:

- OpenAI Agents support stayed intentionally thin and optional; it uses the same session-backed pattern as the LangGraph and CrewAI adapters without introducing any extra framework dependency.

## Step 10 — Sync docs, examples, and contributor flows

Why this exists:

- The project is explicitly aiming for OSS adoption, so the docs and examples are part of the implementation surface.

Files to change:

- `PRD.md`
- `backend/README.md`
- `backend/docs/architecture.md`
- `backend/docs/code-map.md`
- `backend/docs/contributing.md`
- `backend/examples/two_agents.py`
- `backend/examples/server_mode.py`
- `backend/examples/crash_recovery.py`
- `backend/tests/integration/test_layout.py`
- `backend/tests/smoke/test_examples.py`

What will change:

- Sync docs with the actual repo layout and implemented behavior.
- Ensure examples demonstrate the real supported flows.
- Document the quickest install/test path for contributors.

What existing code should be reused:

- current docs structure
- existing examples and smoke tests

What will be verified:

- architecture and code-map docs describe the actual repo
- examples run without stale stub assumptions
- contributor onboarding path works from the documented commands

Which commands prove it passed:

- `cd backend && python -m pytest tests/integration/test_layout.py tests/smoke/test_examples.py`
- `cd backend && python -m compileall src tests examples`

Implementation note after execution:

- The docs now advertise only the commands that actually work today, including `python -m memsmith` after installation and the real example flows.
- The example entrypoints accept overridable data directories so smoke tests and contributors can run them without cross-test or cross-run state collisions.

# Step-level acceptance criteria

- Step 1 is complete when the public SDK contract is explicit, timestamp-capable history exists, and the local happy path still passes.
- Step 2 is complete when `ShardStore` is truly sharded and tested as such.
- Step 3 is complete when wait semantics are regression-tested and lock contention works across agents for the same logical lock key.
- Step 4 is complete when local mutations create durable WAL artifacts on disk.
- Step 5 is complete when `resume()` reconstructs state from real persistence artifacts.
- Step 6 is complete when `memsmith dump` produces stable, timestamped, human-readable output from real session history.
- Step 7 is complete when local watch streams are emitted from real session events and can be consumed through the CLI path.
- Step 8 is complete when a remote client talks to an actual FastAPI server while preserving core semantics.
- Step 9 is complete when LangGraph and CrewAI adapters call through to real core behavior instead of placeholder dataclasses.
- Step 10 is complete when docs and examples match the implementation and the documented contributor path is executable.

# Test strategy

- Unit tests should cover the smallest state, wait, lock, formatting, and persistence primitives.
- Integration tests should cover boundary wiring between session/state/persistence, CLI/observability, and server/client paths.
- Smoke tests should exercise examples and the user-visible happy paths.
- Regression tests are required for:
  - version-aware `wait_for` semantics
  - cross-agent lock contention
  - resume/recovery correctness
  - server-mode parity once transport exists
- Performance/behavior checks should be targeted and mostly manual/local for:
  - sharded store contention behavior
  - WAL flush behavior under bursts of writes
  - checkpoint/recovery latency for moderate session sizes
  - watch stream responsiveness
- No frontend, SQL database, or Neo4j tests are applicable in the current repo.

# Test matrix

| ID | Level | Purpose | Files or commands | Expected pass condition |
|---|---|---|---|---|
| T01 | Unit | Top-level package API stays stable | `backend/tests/unit/test_public_api.py` | `session`, `connect`, `resume`, and version export still work |
| T02 | Unit | Local push/get/wait/lock happy path | `backend/tests/unit/test_session_flow.py` | Current local SDK flow still passes |
| T03 | Unit | Real sharding and versioning | `[Create] backend/tests/unit/test_shard_store.py` | Shard routing, version increments, and snapshot reads pass |
| T04 | Unit | Waiter semantics and timeout behavior | `[Create] backend/tests/unit/test_waiters.py` | Immediate resolve, timeout, and after-version waits pass |
| T05 | Unit | Lock conflict and release behavior | `[Create] backend/tests/unit/test_locks.py` | Cross-agent lock contention and cleanup pass |
| T06 | Unit | WAL entry encoding/decoding and append order | `[Create] backend/tests/unit/test_wal.py` | WAL round-trip and ordering pass |
| T07 | Unit | History and dump formatting | `[Create] backend/tests/unit/test_history_format.py` | Dump lines include expected timestamp and metadata fields |
| T08 | Integration | Session -> state -> waiter wiring | `[Create] backend/tests/integration/test_state_semantics.py` | Multi-agent waits and versions behave correctly |
| T09 | Integration | Session -> persistence -> recovery wiring | `[Create] backend/tests/integration/test_persistence_recovery.py` | Checkpoint + WAL replay restore expected state |
| T10 | Integration | Session -> CLI dump wiring | `[Create] backend/tests/integration/test_cli_dump.py` | CLI dump renders real session history |
| T11 | Integration | Session -> watch stream wiring | `[Create] backend/tests/integration/test_watch_stream.py` | Stream envelopes emit expected sequence |
| T12 | Integration | Server app -> remote client parity | `[Create] backend/tests/integration/test_server_transport.py` | Remote push/get/wait/history paths match local semantics |
| T13 | Integration | Adapter seams | `[Create] backend/tests/integration/test_integrations.py` | LangGraph and CrewAI adapters delegate to MemSmith core |
| T14 | Smoke | Two-agent local example | `backend/tests/smoke/test_examples.py` and `backend/examples/two_agents.py` | Example returns expected papers list |
| T15 | Smoke | Crash recovery example | `backend/examples/crash_recovery.py` | Recovery example proves real restored state |
| T16 | Smoke | Server mode example | `backend/examples/server_mode.py` and `[Create] backend/tests/smoke/test_server_mode.py` | Remote example uses real transport |
| T17 | Perf/Behavior | Shard contention sanity check | local/manual script under `backend/examples/` or ad hoc command | No corruption, no deadlock, expected version ordering |
| T18 | Perf/Behavior | Recovery latency sanity check | local/manual checkpoint + resume command | Recovery remains acceptable for moderate session sizes |
| T19 | Perf/Behavior | Watch responsiveness | local/manual `memsmith watch` against active example | UI updates appear promptly without blocking writes |
| T20 | Docs/Smoke | Contributor path and compilation | `cd backend && python -m compileall src tests examples` | Package, tests, and examples all compile |

# Validation commands

Initial setup:

```bash
cd backend
pip install -e .[dev,server,watch]
```

Targeted validation commands:

```bash
cd backend
python -m pytest tests/unit/test_public_api.py tests/unit/test_session_flow.py
python -m pytest tests/unit/test_shard_store.py tests/unit/test_waiters.py tests/unit/test_locks.py tests/unit/test_wal.py tests/unit/test_history_format.py
python -m pytest tests/integration/test_state_semantics.py tests/integration/test_persistence_recovery.py tests/integration/test_cli_dump.py tests/integration/test_watch_stream.py tests/integration/test_server_transport.py tests/integration/test_integrations.py
python -m pytest tests/smoke/test_examples.py tests/smoke/test_server_mode.py
python examples/two_agents.py
python examples/crash_recovery.py
python examples/server_mode.py
python -m compileall src tests examples
```

Manual/local validation commands for high-risk behavior:

```bash
cd backend
python -m memsmith dump two-agent-demo
python -m memsmith watch two-agent-demo
python -m memsmith serve --host 127.0.0.1 --port 7117
```

## Validation log

- 2026-05-13 20:58:15 IST: `cd backend && PYTHONPATH=src /Users/Sameer/Yashsmith/memsmith/.venv/bin/python -m pytest tests/unit/test_public_api.py tests/unit/test_session_flow.py && PYTHONPATH=src /Users/Sameer/Yashsmith/memsmith/.venv/bin/python examples/two_agents.py` failed because `pytest` was not installed in the configured virtual environment.
- 2026-05-13 20:58:27 IST: Installed missing step-1 test dependencies with `install_python_packages` for `pytest` and `pytest-asyncio`.
- 2026-05-13 20:58:35 IST: `cd backend && PYTHONPATH=src /Users/Sameer/Yashsmith/memsmith/.venv/bin/python -m pytest tests/unit/test_public_api.py tests/unit/test_session_flow.py && PYTHONPATH=src /Users/Sameer/Yashsmith/memsmith/.venv/bin/python examples/two_agents.py` passed. Result: 5 unit tests passed and `examples/two_agents.py` printed `['paper-a', 'paper-b']`.
- 2026-05-13 21:01:33 IST: `cd backend && PYTHONPATH=src /Users/Sameer/Yashsmith/memsmith/.venv/bin/python -m pytest tests/unit/test_shard_store.py tests/integration/test_state_semantics.py tests/unit/test_session_flow.py` passed. Result: 6 tests passed covering shard routing, version increments, snapshot behavior, and the existing local wait/push flow.
- 2026-05-13 21:03:41 IST: `cd backend && PYTHONPATH=src /Users/Sameer/Yashsmith/memsmith/.venv/bin/python -m pytest tests/unit/test_waiters.py tests/unit/test_locks.py tests/unit/test_session_flow.py` passed. Result: 9 tests passed covering immediate wait resolution, `after_version` waiting, timeout behavior, cross-agent lock visibility, lock waiting, and local history semantics.
- 2026-05-13 21:05:30 IST: `cd backend && PYTHONPATH=src /Users/Sameer/Yashsmith/memsmith/.venv/bin/python -m pytest tests/unit/test_wal.py tests/integration/test_wal_flow.py` failed during collection because `msgspec` was not installed in the configured virtual environment.
- 2026-05-13 21:05:42 IST: Installed missing step-4 dependency with `install_python_packages` for `msgspec`.
- 2026-05-13 21:06:01 IST: `cd backend && PYTHONPATH=src /Users/Sameer/Yashsmith/memsmith/.venv/bin/python -m pytest tests/unit/test_wal.py tests/integration/test_wal_flow.py` passed. Result: 2 tests passed covering WAL append order, msgpack round-trip decoding, and durable session push artifacts under the session home.
- 2026-05-13 21:09:21 IST: `cd backend && PYTHONPATH=src /Users/Sameer/Yashsmith/memsmith/.venv/bin/python -m pytest tests/integration/test_persistence_recovery.py tests/smoke/test_examples.py` passed. Result: 3 tests passed covering checkpoint file creation, checkpoint JSON sidecars, recovery from `resume()`, WAL replay after checkpoint, and the crash-recovery example entrypoint.
- 2026-05-13 21:09:32 IST: `cd backend && PYTHONPATH=src /Users/Sameer/Yashsmith/memsmith/.venv/bin/python examples/crash_recovery.py` passed. Result: printed `checkpointed`, proving the example restores persisted state rather than only returning a recovery flag.
- 2026-05-13 21:13:24 IST: `cd backend && PYTHONPATH=src /Users/Sameer/Yashsmith/memsmith/.venv/bin/python -m pytest tests/unit/test_history_format.py tests/integration/test_cli_dump.py` passed. Result: 3 tests passed covering relative timestamp formatting, PRD-style checkpoint rendering, CLI dump timeline output, and JSON export with rendered lines.
- 2026-05-13 21:13:35 IST: `cd backend && PYTHONPATH=src /Users/Sameer/Yashsmith/memsmith/.venv/bin/python -m pytest tests/unit/test_session_flow.py` passed. Result: 3 tests passed confirming the updated `Session.export()` path preserved the existing local session flow and JSON history export behavior.
- 2026-05-13 21:16:30 IST: `cd backend && PYTHONPATH=src /Users/Sameer/Yashsmith/memsmith/.venv/bin/python -m pytest tests/integration/test_watch_stream.py` passed. Result: 2 tests passed covering in-process stream ordering for lock/push/broadcast flows and persisted WAL observation for the local watch consumer.
- 2026-05-13 21:17:54 IST: `cd backend && PYTHONPATH=src /Users/Sameer/Yashsmith/memsmith/.venv/bin/python -m memsmith watch cli-watch --data-dir <tmpdir> --limit 2 --idle-timeout-ms 500` passed after creating a temporary persisted session. Result: the CLI printed live watch lines for `PUSH` and `BROADCAST` events through the package entrypoint.
- 2026-05-13 21:25:05 IST: `cd backend && PYTHONPATH=src /Users/Sameer/Yashsmith/memsmith/.venv/bin/python -m pytest tests/integration/test_server_transport.py tests/smoke/test_server_mode.py` failed during collection because `fastapi` was not installed and the initial server package import boundary still pulled it in eagerly.
- 2026-05-13 21:25:33 IST: Installed missing step-8 server dependencies with `install_python_packages` for `fastapi` and `uvicorn`.
- 2026-05-13 21:27:22 IST: `cd backend && PYTHONPATH=src /Users/Sameer/Yashsmith/memsmith/.venv/bin/python -m pytest tests/integration/test_server_transport.py tests/smoke/test_server_mode.py` passed. Result: 2 tests passed covering health/readiness endpoints, remote push/get/wait semantics against a running server, and the server-mode example behavior through actual HTTP transport.
- 2026-05-13 21:27:31 IST: `cd backend && PYTHONPATH=src /Users/Sameer/Yashmith/memsmith/.venv/bin/python examples/server_mode.py` passed. Result: printed `connected`, proving the example now starts a temporary local server and uses the remote client over the real transport path.
- 2026-05-13 21:28:40 IST: `cd backend && PYTHONPATH=src /Users/Sameer/Yashmith/memsmith/.venv/bin/python -m pytest tests/integration/test_integrations.py` passed. Result: 1 integration test passed proving the LangGraph, CrewAI, and OpenAI Agents adapters all delegate into the shared session/checkpoint behavior instead of re-implementing persistence logic.
- 2026-05-13 21:31:46 IST: `cd backend && PYTHONPATH=src /Users/Sameer/Yashmith/memsmith/.venv/bin/python -m pytest tests/integration/test_layout.py tests/smoke/test_examples.py && PYTHONPATH=src /Users/Sameer/Yashmith/memsmith/.venv/bin/python -m compileall src tests examples` passed. Result: 3 tests passed, the documented docs/examples layout matched the repo, the local examples still ran, and the documented contributor path compiled cleanly across source, tests, and examples.
- 2026-05-13 21:32:09 IST: `cd backend && PYTHONPATH=src /Users/Sameer/Yashmith/memsmith/.venv/bin/python -m pytest tests/smoke/test_server_mode.py` passed. Result: 1 smoke test passed confirming the docs/example sync did not regress the server transport demo.
- 2026-05-13 21:33:18 IST: `cd backend && PYTHONPATH=src /Users/Sameer/Yashmith/memsmith/.venv/bin/python -m pytest` passed. Result: all 28 backend tests passed in one final regression sweep after the full step-by-step implementation.

# Logging / debugging notes

- Add structured debug logging around `push`, `wait_for`, lock acquisition/release, checkpoint creation, WAL enqueue/flush, and resume/replay boundaries.
- Include session name, agent name, logical key, state key, version, and operation in debug logs.
- Avoid logging full payloads by default; log preview or size metadata instead.
- For WAL and recovery work, log file paths and replay counts.
- For server mode, log session ID, request route, and remote/local transport path at debug level.
- For watch/dump, log stream disconnects, dropped events, and render/update errors.

# Decision log

- 2026-05-13: Implement against the actual `backend/src/memsmith/` modular-monolith layout instead of the older `memsmith/core/` sketch in the PRD.
- 2026-05-13: Keep the in-process SDK as the source of truth and make server mode adapt that behavior, not diverge from it.
- 2026-05-13: Keep tests split into unit, integration, smoke, and targeted local/manual perf checks rather than building benchmark-heavy default CI.
- 2026-05-13: Keep persistence file-based under `.memsmith/` rather than introducing SQL or graph storage.
- 2026-05-13 20:59:00 IST: For Step 1, add explicit `Session.state_key(...)` and `Session.lock_key(...)` helper boundaries now, but keep lock behavior unchanged until the dedicated lock-semantics step.
- 2026-05-13 20:59:00 IST: Add `timestamp_ns` to `HistoryEvent` and session runtime metadata (`transport`, `created_at_ns`, `event_count`, `last_event_at_ns`) instead of introducing a separate lifecycle event stream this early.
- 2026-05-13 21:00:00 IST: Step 2 must include `backend/src/memsmith/session/agent.py` because `AgentContext.push()` is the only current caller of `ShardStore.set()`, so a real async sharded store cannot be implemented without updating that call site.
- 2026-05-13 21:01:33 IST: Keep `ShardStore.get()` and `ShardStore.version()` synchronous, but make `ShardStore.set()` async and shard-locked. Because the write path has no internal awaits once the shard lock is held, read calls can stay simple while still avoiding partial writes on the event loop.
- 2026-05-13 21:01:33 IST: Implement `ShardStore.snapshot()` by acquiring all shard locks in stable order, copying state, and releasing in reverse order so later checkpoint/export work can read a consistent snapshot.
- 2026-05-13 21:03:41 IST: Make lock targets session-scoped by logical key through `Session.lock_key(...)` so different agents can contend on the same draft/tool key without changing state-key semantics.
- 2026-05-13 21:03:41 IST: Make `LockRegistry` reentrant for the same owner and timeout-based for different owners. `try_lock()` remains the non-blocking conflict inspection path.
- 2026-05-13 21:06:01 IST: Encode WAL entries as length-prefixed msgpack frames so the log stays append-only and stream-readable without newline-sensitive parsing.
- 2026-05-13 21:06:01 IST: Keep WAL durability behind a background flush thread with an explicit `flush()` / `close()` lifecycle, so session code only enqueues entries and tests can force durable state when needed.
- 2026-05-13 21:07:00 IST: Step 5 must include `backend/src/memsmith/state/shard_store.py` because recovery needs a direct restore path that preserves versions without replaying through `AgentContext.push()` and duplicating WAL writes.
- 2026-05-13 21:09:32 IST: Store checkpoints as msgpack snapshots plus JSON sidecars. The binary snapshot is for exact recovery, while the sidecar keeps the artifact inspectable for contributors and future tooling.
- 2026-05-13 21:09:32 IST: Recovery should restore the latest checkpoint first, then replay only later `PUSH` WAL entries using the recorded last-WAL timestamp. This preserves state versions without re-emitting writes into the WAL.
- 2026-05-13 21:13:35 IST: Make `memsmith dump` reconstruct timelines from persisted WAL/checkpoint artifacts instead of live in-memory history, so the CLI remains useful across process boundaries and after recovery.
- 2026-05-13 21:13:35 IST: Keep JSON history export as a list of structured event objects, but add a rendered `line` field so the same artifact is both machine-readable and quick to inspect by hand.
- 2026-05-13 21:17:54 IST: Split watch into two seams: `Session.record_event()` emits non-blocking in-process `StreamEnvelope`s for exact ordering, while the CLI tails the persisted WAL so `watch` already works across processes before server mode lands.
- 2026-05-13 21:17:54 IST: Keep the watch UI intentionally line-oriented for now. The stable contract is the stream envelope and consumer path; a richer TUI can build on that seam later without changing the runtime.
- 2026-05-13 21:27:31 IST: Keep the remote transport adapter thin by using the local `Session` runtime as the server-side source of truth and a standard-library HTTP client wrapped with `asyncio.to_thread` on the client side.
- 2026-05-13 21:27:31 IST: Keep server imports optional by making `memsmith.server` lazy. The remote client does not need FastAPI to exist just to be imported.
- 2026-05-13 21:28:40 IST: Keep the integration layer boring: adapter objects should only translate framework-specific method names into the existing session API and checkpoint lifecycle, never fork storage or coordination behavior.
- 2026-05-13 21:32:09 IST: Keep contributor docs honest to the currently implemented surface. Document the working example and CLI paths that are executable today rather than promising unfinished scaffolds like `cli serve`.
- 2026-05-13 21:32:09 IST: Make examples injectable by data directory so automated smoke tests and humans can reuse them without hidden state coupling.

# Surprises / discoveries

- 2026-05-13: The scaffold already supports a meaningful local happy path; the plan should extend it rather than rewrite it.
- 2026-05-13: `LockRegistry` currently works on agent-prefixed state keys through `AgentContext.lock()`, so different agents do not currently contend for the same logical key.
- 2026-05-13: `resume()` is a stub that only sets `recovered=True`.
- 2026-05-13: `connect()` is a stub that returns a local `Session` without remote transport.
- 2026-05-13: `server/app.py` is currently metadata-only and not a FastAPI app.
- 2026-05-13: History events lack timestamps even though the PRD and dump spec require them.
- 2026-05-13: The PRD architecture tree still names a `memsmith/core/` layout that does not match the current repo structure.
- 2026-05-13 20:58:15 IST: The configured project virtual environment did not have `pytest` installed, so step execution needed a one-time environment repair before tests could run.
- 2026-05-13 21:00:00 IST: The original step-2 file list missed `backend/src/memsmith/session/agent.py`, which must change if store writes become truly shard-locked and async.
- 2026-05-13 21:01:33 IST: The current event-loop-only design made a real shard-locked store easier than expected, because no cross-thread coordination was needed yet for store reads/writes.
- 2026-05-13 21:03:41 IST: The existing `wait_for()` implementation already satisfied the core version-aware semantics once it was exercised with explicit `after_version` tests, so step 3 only needed lock-path code changes.
- 2026-05-13 21:05:30 IST: The virtual environment also lacked `msgspec`, even though it is declared in `backend/pyproject.toml`; step 4 needed a one-time dependency repair before WAL tests could import the persistence layer.
- 2026-05-13 21:07:00 IST: The original step-5 file list missed `backend/src/memsmith/state/shard_store.py`; durable recovery needs a restore path below the public agent API to avoid appending replayed state back into the WAL.
- 2026-05-13 21:09:32 IST: The existing scaffold made a clean checkpoint/replay split straightforward because `StateValue` already carried the version needed for exact restore semantics.
- 2026-05-13 21:13:35 IST: The persisted debug story can be implemented entirely from WAL plus checkpoint metadata; no separate history database or side log was needed for the CLI dump path.
- 2026-05-13 21:17:12 IST: The planned manual watch command exposed a small packaging gap: without `backend/src/memsmith/__main__.py`, `python -m memsmith ...` could not execute the CLI even though the command handlers themselves were already working.
- 2026-05-13 21:25:05 IST: The initial server implementation accidentally made `fastapi` a hard import-time dependency for the whole package because `memsmith.api` reached `memsmith.server.client`, which first executed `memsmith.server.__init__`.
- 2026-05-13 21:26:31 IST: The old `server.routes` package initializer and a malformed pre-existing `server/schemas.py` tail both surfaced only once the real FastAPI modules were imported, so step 8 needed a small round of local boundary cleanup before the transport tests could run.
- 2026-05-13 21:28:40 IST: The placeholder integration modules were easier to replace than extend; none of them had real framework coupling yet, so a direct session-backed adapter kept the seam obvious and testable.
- 2026-05-13 21:32:09 IST: The final docs sync was narrower than expected: the biggest drift was not prose quality but stale commands and the old internal tree in the PRD.

# Tracker table

| # | Phase | Step | Files | Code | Unit | Integration | Smoke | Perf/Docs | Done |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Core SDK | Harden SDK contract and event model | `backend/src/memsmith/api.py`, `backend/src/memsmith/session/manager.py`, `backend/src/memsmith/session/agent.py`, `backend/src/memsmith/types.py`, `backend/tests/unit/test_public_api.py`, `backend/tests/unit/test_session_flow.py` | [x] | [x] | n/a | [x] | n/a | [x] |
| 2 | State semantics | Implement real sharded store | `backend/src/memsmith/state/shard_store.py`, `backend/src/memsmith/session/manager.py`, `backend/src/memsmith/session/agent.py`, `[Create] backend/tests/unit/test_shard_store.py`, `[Create] backend/tests/integration/test_state_semantics.py` | [x] | [x] | [x] | n/a | n/a | [x] |
| 3 | State semantics | Finalize wait and lock behavior | `backend/src/memsmith/state/waiters.py`, `backend/src/memsmith/state/locks.py`, `backend/src/memsmith/session/agent.py`, `[Create] backend/tests/unit/test_waiters.py`, `[Create] backend/tests/unit/test_locks.py` | [x] | [x] | n/a | n/a | n/a | [x] |
| 4 | Reliability | Implement file-backed WAL | `backend/src/memsmith/persistence/wal.py`, `backend/src/memsmith/persistence/paths.py`, `backend/src/memsmith/session/manager.py`, `[Create] backend/tests/unit/test_wal.py`, `[Create] backend/tests/integration/test_wal_flow.py` | [x] | [x] | [x] | n/a | n/a | [x] |
| 5 | Reliability | Implement checkpoints and recovery | `backend/src/memsmith/persistence/checkpoint.py`, `backend/src/memsmith/persistence/recovery.py`, `backend/src/memsmith/session/manager.py`, `backend/src/memsmith/api.py`, `backend/src/memsmith/state/shard_store.py`, `backend/examples/crash_recovery.py`, `[Create] backend/tests/integration/test_persistence_recovery.py` | [x] | n/a | [x] | [x] | n/a | [x] |
| 6 | Observability | Implement dump export and CLI | `backend/src/memsmith/observability/history.py`, `backend/src/memsmith/session/manager.py`, `backend/src/memsmith/cli/commands/dump.py`, `[Create] backend/tests/unit/test_history_format.py`, `[Create] backend/tests/integration/test_cli_dump.py` | [x] | [x] | [x] | n/a | n/a | [x] |
| 7 | Observability | Implement local watch stream and TUI | `backend/src/memsmith/observability/streams.py`, `[Create] backend/src/memsmith/observability/watch.py`, `backend/src/memsmith/session/manager.py`, `backend/src/memsmith/cli/commands/watch.py`, `backend/src/memsmith/__main__.py`, `[Create] backend/tests/integration/test_watch_stream.py` | [x] | n/a | [x] | [x] | n/a | [x] |
| 8 | Transport | Implement FastAPI server and remote client | `backend/src/memsmith/server/app.py`, `backend/src/memsmith/server/__init__.py`, `backend/src/memsmith/server/routes/*`, `backend/src/memsmith/server/ws.py`, `[Create] backend/src/memsmith/server/client.py`, `backend/examples/server_mode.py`, `[Create] backend/tests/integration/test_server_transport.py`, `[Create] backend/tests/smoke/test_server_mode.py` | [x] | n/a | [x] | [x] | n/a | [x] |
| 9 | Integrations | Implement LangGraph and CrewAI adapters | `backend/src/memsmith/integrations/langgraph.py`, `backend/src/memsmith/integrations/crewai.py`, `backend/src/memsmith/integrations/openai_agents.py`, `[Create] backend/tests/integration/test_integrations.py` | [x] | n/a | [x] | n/a | n/a | [x] |
| 10 | OSS polish | Sync docs, examples, and contributor flows | `PRD.md`, `backend/README.md`, `backend/docs/*.md`, `backend/examples/*.py`, `backend/tests/integration/test_layout.py`, `backend/tests/smoke/test_examples.py` | [x] | n/a | [x] | [x] | [x] | [x] |

# Open questions / risks

- Should locks be fully session-scoped by logical key, or should the API support both agent-scoped and session-scoped lock targets?
- Should `wait_for()` return the payload only, or a richer object with version metadata for advanced callers?
- How much of `memsmith watch` needs to be automated versus locally smoke-tested, given TUI complexity?
- Should server-mode streaming use WebSocket only, or should SSE be considered for simpler remote watch behavior?
- How should WAL flush frequency be tuned for local developer ergonomics versus durability expectations?
- Does the first usable release need the OpenAI Agents adapter, or should it remain explicitly deferred after LangGraph and CrewAI?
- Should the PRD architecture tree be updated as part of execution or preserved as a higher-level sketch with backend docs carrying the actual file map?