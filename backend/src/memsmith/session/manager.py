"""Owns session lifecycle and wires together shared state primitives."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from time import time_ns
from typing import Any

from memsmith.observability.streams import StreamEnvelope
from memsmith.observability.history import write_json_history
from memsmith.persistence.checkpoint import CheckpointWriter
from memsmith.persistence.paths import session_home, wal_path
from memsmith.persistence.recovery import build_recovery_plan, replayable_entries
from memsmith.persistence.wal import WAL
from memsmith.state.locks import LockRegistry
from memsmith.state.shard_store import ShardStore
from memsmith.state.waiters import WaitRegistry
from memsmith.types import HistoryEvent, StateValue

_UNSET = object()


@dataclass(slots=True)
class Session:
    """In-process MemSmith session scaffold.

    This is intentionally small: contributors should be able to understand the
    main data flow from this file and step outward into state, persistence, or
    server code as needed.
    """

    name: str
    data_dir: Path | None = None
    remote_host: str | None = None
    transport: str = "local"
    recovered: bool = False
    created_at_ns: int = field(default_factory=time_ns)
    store: ShardStore = field(default_factory=ShardStore)
    locks: LockRegistry = field(default_factory=LockRegistry)
    waiters: WaitRegistry = field(default_factory=WaitRegistry)
    session_home: Path = field(init=False)
    wal: WAL = field(init=False)
    checkpoint_writer: CheckpointWriter = field(init=False)
    event_count: int = field(default=0, init=False)
    last_event_at_ns: int = field(default=0, init=False)
    _history: list[HistoryEvent] = field(default_factory=list, init=False)
    _subscribers: list[asyncio.Queue[StreamEnvelope]] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.session_home = session_home(self.name, base_dir=self.data_dir)
        self.session_home.mkdir(parents=True, exist_ok=True)
        self.wal = WAL(path=wal_path(self.name, base_dir=self.data_dir))
        self.checkpoint_writer = CheckpointWriter(session_name=self.name, base_dir=self.data_dir)
        self.last_event_at_ns = self.created_at_ns

    def agent(self, agent_name: str) -> "AgentContext":
        from memsmith.session.agent import AgentContext

        return AgentContext(session=self, name=agent_name)

    def state_key(self, agent_name: str, key: str) -> str:
        return f"{agent_name}:{key}"

    def lock_key(self, agent_name: str, key: str) -> str:
        return key

    def full_key(self, agent_name: str, key: str) -> str:
        return self.state_key(agent_name, key)

    def preview(self, value: Any) -> str:
        return repr(value)[:80]

    def value_size_bytes(self, value: Any) -> int:
        return len(repr(value).encode("utf-8"))

    def record_event(
        self,
        operation: str,
        *,
        agent: str,
        key: str,
        version: int = 0,
        value: Any | None = None,
    ) -> HistoryEvent:
        recorded_at_ns = time_ns()
        preview = None if value is None else self.preview(value)
        self.event_count += 1
        self.last_event_at_ns = recorded_at_ns
        event = HistoryEvent(
            timestamp_ns=recorded_at_ns,
            operation=operation,
            agent=agent,
            key=key,
            version=version,
            value_preview=preview,
            value_size_bytes=0 if value is None else self.value_size_bytes(value),
        )
        self._history.append(event)
        self._publish_event(event)
        return event

    def record_persisted_event(
        self,
        operation: str,
        *,
        agent: str,
        key: str,
        version: int = 0,
        value: Any | None = None,
        wal_value: Any = _UNSET,
    ) -> HistoryEvent:
        event = self.record_event(
            operation,
            agent=agent,
            key=key,
            version=version,
            value=value,
        )
        persisted_value = value if wal_value is _UNSET else wal_value
        self.wal.append(
            operation,
            self._wal_key_for_event(event),
            persisted_value,
            version=event.version or self.event_count,
        )
        return event

    def _wal_key_for_event(self, event: HistoryEvent) -> str:
        if event.agent == "session":
            return event.key
        return f"{event.agent}:{event.key}"

    async def notify(self, key: str) -> None:
        condition = self.waiters.for_key(key)
        async with condition:
            condition.notify_all()

    async def broadcast(self, event: str, *, payload: Any | None = None) -> None:
        self.record_persisted_event("BROADCAST", agent="session", key=event, value=payload)

    async def history(self) -> list[HistoryEvent]:
        return list(self._history)

    async def snapshot_state(self) -> dict[str, StateValue]:
        return await self.store.snapshot()

    async def checkpoint(self, label: str) -> None:
        self.flush_wal()
        snapshot = await self.snapshot_state()
        last_wal_timestamp_ns = self.wal.entries[-1].timestamp_ns if self.wal.entries else 0
        self.checkpoint_writer.write(
            label,
            snapshot=snapshot,
            created_at_ns=self.created_at_ns,
            event_count=self.event_count,
            last_wal_timestamp_ns=last_wal_timestamp_ns,
        )
        self.record_persisted_event(
            "CHECKPOINT",
            agent="session",
            key=label,
            value=str(self.checkpoint_writer.path_for(label)),
            wal_value={"path": str(self.checkpoint_writer.path_for(label))},
        )

    async def export(self, path: str | Path) -> Path:
        return write_json_history(path, self._history)

    def flush_wal(self) -> None:
        self.wal.flush()

    def close(self) -> None:
        self.wal.close()

    def subscribe(self) -> asyncio.Queue[StreamEnvelope]:
        queue: asyncio.Queue[StreamEnvelope] = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[StreamEnvelope]) -> None:
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    async def recover(self) -> None:
        plan = build_recovery_plan(self.name, base_dir=self.data_dir)
        checkpoint_timestamp_ns = 0

        if plan.checkpoint_path is not None:
            checkpoint = self.checkpoint_writer.read(plan.checkpoint_path)
            await self.store.restore({state.key: state for state in checkpoint.states})
            self.created_at_ns = checkpoint.created_at_ns
            self.event_count = checkpoint.event_count
            self.last_event_at_ns = checkpoint.checkpointed_at_ns
            checkpoint_timestamp_ns = checkpoint.last_wal_timestamp_ns

        if plan.wal_path is not None:
            for entry in replayable_entries(self.wal.read_entries(), after_timestamp_ns=checkpoint_timestamp_ns):
                await self.store.put_state(
                    StateValue(key=entry.key, value=entry.value, version=entry.version)
                )

    def _publish_event(self, event: HistoryEvent) -> None:
        envelope = StreamEnvelope(session_name=self.name, sequence=self.event_count, event=event)
        for subscriber in list(self._subscribers):
            subscriber.put_nowait(envelope)
