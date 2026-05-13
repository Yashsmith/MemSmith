"""History formatting helpers."""

from __future__ import annotations

from memsmith.types import HistoryEvent


def format_event(event: HistoryEvent) -> str:
    """Render a single history event in a dump-friendly format."""
    preview = "" if event.value_preview is None else f" {event.value_preview}"
    return f"{event.agent} {event.operation} {event.key} v{event.version}{preview}".strip()
