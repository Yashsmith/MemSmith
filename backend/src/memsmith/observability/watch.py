"""Local watch stream helpers."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from memsmith.observability.history import format_event
from memsmith.observability.streams import StreamEnvelope
from memsmith.persistence.paths import wal_path
from memsmith.persistence.wal import WAL, WALEntry
from memsmith.types import HistoryEvent

if TYPE_CHECKING:
    from memsmith.session.manager import Session


@dataclass(slots=True)
class LocalWatchSubscription:
    """Collects live stream envelopes from an in-process session."""

    session: Session
    queue: asyncio.Queue[StreamEnvelope]

    async def collect(self, *, limit: int | None = None, timeout_ms: int = 1_000) -> list[StreamEnvelope]:
        envelopes: list[StreamEnvelope] = []

        while limit is None or len(envelopes) < limit:
            try:
                envelope = await asyncio.wait_for(self.queue.get(), timeout=timeout_ms / 1000)
            except TimeoutError:
                break
            envelopes.append(envelope)

        return envelopes

    def close(self) -> None:
        self.session.unsubscribe(self.queue)


def subscribe(session: Session) -> LocalWatchSubscription:
    return LocalWatchSubscription(session=session, queue=session.subscribe())


@dataclass(slots=True)
class PersistedWatchConsumer:
    """Polls the persisted WAL so watch works across process boundaries."""

    session_name: str
    data_dir: str | Path | None = None

    async def collect(
        self,
        *,
        limit: int | None = None,
        idle_timeout_ms: int = 2_000,
        poll_interval_ms: int = 50,
    ) -> list[StreamEnvelope]:
        path = wal_path(self.session_name, base_dir=self.data_dir)
        loop = asyncio.get_running_loop()
        last_activity = loop.time()
        seen = 0
        envelopes: list[StreamEnvelope] = []

        while True:
            if path.exists():
                entries = WAL(path=path).read_entries()
                new_entries = entries[seen:]
                if new_entries:
                    envelopes.extend(_envelopes_from_entries(self.session_name, new_entries, start_sequence=seen + 1))
                    seen += len(new_entries)
                    last_activity = loop.time()
                    if limit is not None and len(envelopes) >= limit:
                        return envelopes[:limit]

            if envelopes and (loop.time() - last_activity) * 1000 >= idle_timeout_ms:
                return envelopes

            if not envelopes and (loop.time() - last_activity) * 1000 >= idle_timeout_ms:
                return []

            await asyncio.sleep(poll_interval_ms / 1000)


@dataclass(slots=True)
class WatchSnapshot:
    """Structured watch view grouped by actor."""

    session_name: str
    columns: dict[str, list[HistoryEvent]] = field(default_factory=dict)
    total_events: int = 0

    @property
    def agents(self) -> list[str]:
        return [name for name in self.columns if name != "SESSION"]


def build_watch_snapshot(session_name: str, envelopes: list[StreamEnvelope]) -> WatchSnapshot:
    snapshot = WatchSnapshot(session_name=session_name, total_events=len(envelopes))
    for envelope in envelopes:
        actor = "SESSION" if envelope.event.agent == "session" else envelope.event.agent
        snapshot.columns.setdefault(actor, []).append(envelope.event)
    return snapshot


def render_watch(session_name: str, envelopes: list[StreamEnvelope]) -> str:
    snapshot = build_watch_snapshot(session_name, envelopes)
    agents = ", ".join(snapshot.agents) if snapshot.agents else "none"
    header = [
        f"MemSmith Watch: {session_name}",
        f"Events: {snapshot.total_events} | Agents: {len(snapshot.agents)} ({agents})",
        "-" * 41,
    ]
    if not envelopes:
        return "\n".join([*header, "No events observed."])

    session_start_ns = min(envelope.event.timestamp_ns for envelope in envelopes)
    body: list[str] = []
    for actor, events in snapshot.columns.items():
        body.append(f"[{actor}]")
        for event in events:
            body.append(f"  {format_event(event, session_start_ns=session_start_ns)}")
    rendered = "\n".join([*header, *body])
    return rendered


def _envelopes_from_entries(
    session_name: str,
    entries: list[WALEntry],
    *,
    start_sequence: int,
) -> list[StreamEnvelope]:
    envelopes: list[StreamEnvelope] = []
    for offset, entry in enumerate(entries, start=start_sequence):
        agent, key = _display_actor_and_key(entry)
        preview = _preview(entry)
        event = HistoryEvent(
            timestamp_ns=entry.timestamp_ns,
            operation=entry.operation,
            agent=agent,
            key=key,
            version=entry.version,
            value_preview=preview,
            value_size_bytes=0 if entry.value is None else len(repr(entry.value).encode("utf-8")),
        )
        envelopes.append(StreamEnvelope(session_name=session_name, sequence=offset, event=event))
    return envelopes


def _display_actor_and_key(entry: WALEntry) -> tuple[str, str]:
    if entry.operation == "PUSH" and ":" in entry.key:
        agent, key = entry.key.split(":", 1)
        return agent, key
    if entry.operation in {
        "GET",
        "WAIT_FOR",
        "WAIT_FOR_RESOLVE",
        "WAIT_FOR_TIMEOUT",
        "LOCK_ACQUIRE",
        "LOCK_RELEASE",
        "LOCK_TIMEOUT",
    } and ":" in entry.key:
        agent, key = entry.key.split(":", 1)
        return agent, key
    if entry.operation == "CHECKPOINT" and isinstance(entry.value, dict):
        return "session", str(entry.value.get("path", entry.key))
    return "session", entry.key


def _preview(entry: WALEntry) -> str | None:
    if entry.value is None:
        return None
    if entry.operation == "CHECKPOINT" and isinstance(entry.value, dict):
        path = entry.value.get("path")
        return str(path) if path is not None else None
    return repr(entry.value)[:80]
