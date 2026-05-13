"""Public constructors for local, recovered, and remote sessions."""

from __future__ import annotations

from pathlib import Path

from memsmith.server.client import RemoteSession
from memsmith.session.manager import Session


def session(name: str, *, data_dir: str | Path | None = None) -> Session:
    """Start an in-process MemSmith session."""
    return Session(name=name, data_dir=Path(data_dir) if data_dir else None, transport="local")


async def connect(name: str, *, host: str) -> Session:
    """Connect to a remote MemSmith server.

    This scaffold keeps the same return type as local sessions so the SDK stays stable.
    """
    return RemoteSession(name=name, remote_host=host)


async def resume(name: str, *, data_dir: str | Path | None = None) -> Session:
    """Resume a session from the on-disk recovery path."""
    restored = Session(
        name=name,
        data_dir=Path(data_dir) if data_dir else None,
        transport="local",
        recovered=True,
    )
    await restored.recover()
    return restored
