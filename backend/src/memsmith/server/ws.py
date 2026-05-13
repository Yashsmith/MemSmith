"""WebSocket boundary for remote watch mode."""

from __future__ import annotations


def watch_channel_name(session_name: str) -> str:
    return f"memsmith.watch.{session_name}"
