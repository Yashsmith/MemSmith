from __future__ import annotations

import asyncio
from pathlib import Path

import memsmith
from memsmith.observability.history import history_from_wal
from memsmith.persistence.recovery import replayable_entries


def test_persisted_observability_events_do_not_become_replayable_state(tmp_path: Path) -> None:
    async def scenario() -> tuple[list[str], list[str], str | None]:
        session = memsmith.session("observability-events", data_dir=tmp_path)
        try:
            await session.agent("researcher").push("status", "ready")
            session.record_persisted_event(
                "GET",
                agent="researcher",
                key="researcher:status",
                version=1,
                value="ready",
            )
            session.record_persisted_event(
                "WAIT_FOR",
                agent="writer",
                key="researcher:status",
                wal_value={"after_version": None, "timeout_ms": 30_000},
            )
            session.flush_wal()

            entries = session.wal.read_entries()
            replayable = replayable_entries(entries, after_timestamp_ns=0)
            history = history_from_wal("observability-events", entries)
            return (
                [entry.operation for entry in replayable],
                [event.operation for event in history],
                history[-1].agent,
            )
        finally:
            session.close()

    replayable_operations, history_operations, last_agent = asyncio.run(scenario())

    assert replayable_operations == ["PUSH"]
    assert history_operations == ["SESSION_START", "PUSH", "GET", "WAIT_FOR"]
    assert last_agent == "writer"
