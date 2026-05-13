from __future__ import annotations

import asyncio
from pathlib import Path

import memsmith


def test_local_push_creates_durable_wal_artifacts(tmp_path: Path) -> None:
    async def scenario() -> tuple[bool, list[tuple[str, str, int]]]:
        session = memsmith.session("wal-flow", data_dir=tmp_path)
        try:
            await session.agent("researcher").push("papers", ["paper-a"])
            session.flush_wal()
            entries = session.wal.read_entries()
            return session.wal.path.exists(), [
                (entry.operation, entry.key, entry.version) for entry in entries
            ]
        finally:
            session.close()

    wal_exists, entries = asyncio.run(scenario())
    assert wal_exists is True
    assert entries == [("PUSH", "researcher:papers", 1)]