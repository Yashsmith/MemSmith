"""Schema placeholders for the HTTP transport."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class PushStateRequest:
    session: str
    agent: str
    key: str
    value: Any


@dataclass(slots=True, frozen=True)
class LockResponse:
    locked: bool
    held_by: str | None = None
