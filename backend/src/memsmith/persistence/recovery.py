"""Recovery planning surface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class RecoveryPlan:
    """Documents which persistence artifacts should be replayed."""

    session_name: str
    checkpoint_path: Path | None
    wal_path: Path | None
