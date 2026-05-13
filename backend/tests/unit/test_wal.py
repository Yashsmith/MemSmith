from __future__ import annotations

from pathlib import Path

from memsmith.persistence.wal import WAL


def test_wal_round_trips_entries_in_append_order(tmp_path: Path) -> None:
    wal = WAL(path=tmp_path / "session.wal")
    try:
        wal.append("PUSH", "researcher:papers", ["paper-a"], version=1)
        wal.append("BROADCAST", "pipeline_complete", {"count": 1}, version=2)
        wal.flush()

        entries = wal.read_entries()
        assert [entry.operation for entry in entries] == ["PUSH", "BROADCAST"]
        assert entries[0].key == "researcher:papers"
        assert entries[1].value == {"count": 1}
    finally:
        wal.close()