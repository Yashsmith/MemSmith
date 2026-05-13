"""Event envelopes for future watch and websocket streams."""

from __future__ import annotations

from dataclasses import dataclass

from memsmith.types import HistoryEvent


@dataclass(slots=True, frozen=True)
class StreamEnvelope:
    """Stable payload shape for local and remote event streams."""

    session_name: str
    sequence: int
    event: HistoryEvent
