"""Shared types used across the package."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias

Payload: TypeAlias = Any


@dataclass(slots=True, frozen=True)
class StateValue:
    """Stored state plus its version."""

    key: str
    value: Payload
    version: int


@dataclass(slots=True, frozen=True)
class HistoryEvent:
    """Human-readable event emitted by the session."""

    operation: str
    agent: str
    key: str
    version: int = 0
    value_preview: str | None = None


@dataclass(slots=True, frozen=True)
class LockInfo:
    """Minimal lock status returned by the agent API."""

    key: str
    held_by: str | None = None
    token: str | None = None
