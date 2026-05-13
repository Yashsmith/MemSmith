"""Checkpoint planning helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from memsmith.persistence.paths import session_home


@dataclass(slots=True)
class CheckpointWriter:
    """Resolves checkpoint paths for a session."""

    session_name: str
    base_dir: Path | None = None

    def path_for(self, label: str) -> Path:
        root = session_home(self.session_name, base_dir=self.base_dir)
        return root / f"{label}.checkpoint"
