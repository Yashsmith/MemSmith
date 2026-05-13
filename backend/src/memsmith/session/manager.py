"""Owns session lifecycle and wires together shared state primitives."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from memsmith.state.locks import LockRegistry
from memsmith.state.shard_store import ShardStore
from memsmith.state.waiters import WaitRegistry
from memsmith.types import HistoryEvent


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
    recovered: bool = False
    store: ShardStore = field(default_factory=ShardStore)
    locks: LockRegistry = field(default_factory=LockRegistry)
    waiters: WaitRegistry = field(default_factory=WaitRegistry)
    _history: list[HistoryEvent] = field(default_factory=list, init=False)

    def agent(self, agent_name: str) -> "AgentContext":
        from memsmith.session.agent import AgentContext

        return AgentContext(session=self, name=agent_name)

    def full_key(self, agent_name: str, key: str) -> str:
        return f"{agent_name}:{key}"

    def preview(self, value: Any) -> str:
        return repr(value)[:80]

    def record_event(
        self,
        operation: str,
        *,
        agent: str,
        key: str,
        version: int = 0,
        value: Any | None = None,
    ) -> None:
        preview = None if value is None else self.preview(value)
        self._history.append(
            HistoryEvent(
                operation=operation,
                agent=agent,
                key=key,
                version=version,
                value_preview=preview,
            )
        )

    async def notify(self, key: str) -> None:
        condition = self.waiters.for_key(key)
        async with condition:
            condition.notify_all()

    async def broadcast(self, event: str, *, payload: Any | None = None) -> None:
        self.record_event("BROADCAST", agent="session", key=event, value=payload)

    async def history(self) -> list[HistoryEvent]:
        return list(self._history)

    async def checkpoint(self, label: str) -> None:
        self.record_event("CHECKPOINT", agent="session", key=label)

    async def export(self, path: str | Path) -> Path:
        output_path = Path(path)
        serialized = [asdict(event) for event in self._history]
        output_path.write_text(json.dumps(serialized, indent=2), encoding="utf-8")
        return output_path

