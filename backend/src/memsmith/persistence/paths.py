"""File-system layout helpers for session data."""

from __future__ import annotations

from pathlib import Path


def session_home(session_name: str, *, base_dir: str | Path | None = None) -> Path:
    root = Path(base_dir) if base_dir is not None else Path(".memsmith")
    return root / session_name
