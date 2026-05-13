"""Recovery planning surface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from memsmith.persistence.paths import session_home, wal_path
from memsmith.persistence.wal import WALEntry


@dataclass(slots=True, frozen=True)
class RecoveryPlan:
    """Documents which persistence artifacts should be replayed."""

    session_name: str
    checkpoint_path: Path | None
    wal_path: Path | None


def build_recovery_plan(session_name: str, *, base_dir: Path | None = None) -> RecoveryPlan:
    root = session_home(session_name, base_dir=base_dir)
    checkpoints = sorted(root.glob("*.checkpoint"), key=lambda path: path.stat().st_mtime_ns)
    latest_checkpoint = checkpoints[-1] if checkpoints else None
    session_wal = wal_path(session_name, base_dir=base_dir)
    return RecoveryPlan(
        session_name=session_name,
        checkpoint_path=latest_checkpoint,
        wal_path=session_wal if session_wal.exists() else None,
    )


def replayable_entries(entries: list[WALEntry], *, after_timestamp_ns: int) -> list[WALEntry]:
    return [
        entry
        for entry in entries
        if entry.timestamp_ns > after_timestamp_ns and entry.operation == "PUSH"
    ]
