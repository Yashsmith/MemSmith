from __future__ import annotations

import asyncio
from pathlib import Path

import memsmith
from memsmith.observability.watch import PersistedWatchConsumer, subscribe


def test_runtime_watch_stream_preserves_event_order_for_lock_push_broadcast(tmp_path: Path) -> None:
    async def scenario() -> tuple[list[str], list[int]]:
        session = memsmith.session("watch-runtime", data_dir=tmp_path)
        watcher = subscribe(session)
        try:
            async def producer() -> None:
                async with session.agent("writer").lock("draft"):
                    await session.agent("writer").push("draft", "hello")
                await session.broadcast("pipeline_complete")

            producer_task = asyncio.create_task(producer())
            envelopes = await watcher.collect(limit=4, timeout_ms=1_000)
            await producer_task
            return [envelope.event.operation for envelope in envelopes], [envelope.sequence for envelope in envelopes]
        finally:
            watcher.close()
            session.close()

    operations, sequences = asyncio.run(scenario())
    assert operations == ["LOCK_ACQUIRE", "PUSH", "LOCK_RELEASE", "BROADCAST"]
    assert sequences == [1, 2, 3, 4]


def test_persisted_watch_consumer_reads_new_wal_events(tmp_path: Path) -> None:
    async def scenario() -> list[str]:
        session = memsmith.session("watch-persisted", data_dir=tmp_path)
        consumer = PersistedWatchConsumer(session_name="watch-persisted", data_dir=tmp_path)
        try:
            consumer_task = asyncio.create_task(consumer.collect(limit=2, idle_timeout_ms=1_000))
            await session.agent("researcher").push("papers", ["paper-a"])
            await session.broadcast("pipeline_complete")
            envelopes = await consumer_task
            return [envelope.event.operation for envelope in envelopes]
        finally:
            session.close()

    operations = asyncio.run(scenario())
    assert operations == ["PUSH", "BROADCAST"]