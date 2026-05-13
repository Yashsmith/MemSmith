"""Request and response schemas for server mode."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class PushRequest(BaseModel):
    value: Any


class BroadcastRequest(BaseModel):
    payload: Any | None = None


class WaitRequest(BaseModel):
    after_version: int | None = None
    timeout_ms: int = 30_000


class LockRequest(BaseModel):
    timeout_ms: int = 5_000


class StateResponse(BaseModel):
    value: Any | None = None
    version: int = 0


class CheckpointResponse(BaseModel):
    label: str
    path: str
