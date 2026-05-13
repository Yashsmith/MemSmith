"""Streaming routes for history and watch data."""

from __future__ import annotations

from fastapi import APIRouter, Request

from memsmith.observability.history import serialize_history

router = APIRouter()


@router.get("/sessions/{session}/history")
async def history(session: str, request: Request) -> dict[str, object]:
    runtime = request.app.state.registry.get(session)
    return {"events": serialize_history(await runtime.history())}
