"""HTTP routes for remote session operations."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request

from memsmith.errors import MemSmithTimeoutError
from memsmith.server.schemas import (
    BroadcastRequest,
    CheckpointResponse,
    LockRequest,
    PushRequest,
    StateResponse,
    WaitRequest,
)

router = APIRouter()


def _session(request: Request, session_name: str):
    return request.app.state.registry.get(session_name)


@router.post("/sessions/{session}/agents/{agent}/state/{key}")
async def push_state(
    session: str,
    agent: str,
    key: str,
    payload: PushRequest,
    request: Request,
) -> StateResponse:
    runtime = _session(request, session)
    state = await runtime.agent(agent).push(key, payload.value)
    return StateResponse(value=state.value, version=state.version)


@router.get("/sessions/{session}/agents/{agent}/state/{key}")
async def get_state(session: str, agent: str, key: str, request: Request) -> StateResponse:
    runtime = _session(request, session)
    full_key = runtime.state_key(agent, key)
    state = runtime.store.get(full_key)
    if state is None:
        raise HTTPException(status_code=404, detail="State key not found")
    runtime.record_persisted_event(
        "GET",
        agent=agent,
        key=full_key,
        version=state.version,
        value=state.value,
    )
    return StateResponse(value=state.value, version=state.version)


@router.post("/sessions/{session}/agents/{agent}/wait/{source_agent}/{key}")
async def wait_for_state(
    session: str,
    agent: str,
    source_agent: str,
    key: str,
    payload: WaitRequest,
    request: Request,
) -> StateResponse:
    runtime = _session(request, session)
    try:
        value = await runtime.agent(agent).wait_for(
            source_agent,
            key,
            after_version=payload.after_version,
            timeout_ms=payload.timeout_ms,
        )
    except MemSmithTimeoutError as exc:
        raise HTTPException(status_code=408, detail=str(exc)) from exc

    version = runtime.store.version(runtime.state_key(source_agent, key))
    return StateResponse(value=value, version=version)


@router.post("/sessions/{session}/broadcast/{event}")
async def broadcast_event(
    session: str,
    event: str,
    payload: BroadcastRequest,
    request: Request,
) -> dict[str, str]:
    runtime = _session(request, session)
    await runtime.broadcast(event, payload=payload.payload)
    return {"status": "ok"}


@router.post("/sessions/{session}/checkpoints/{label}")
async def create_checkpoint(session: str, label: str, request: Request) -> CheckpointResponse:
    runtime = _session(request, session)
    await runtime.checkpoint(label)
    return CheckpointResponse(label=label, path=str(runtime.checkpoint_writer.path_for(label)))


@router.post("/sessions/{session}/locks/{agent}/{key}")
async def acquire_lock(
    session: str,
    agent: str,
    key: str,
    payload: LockRequest,
    request: Request,
) -> dict[str, str | None]:
    runtime = _session(request, session)
    try:
        lock_info = await runtime.locks.acquire(
            runtime.lock_key(agent, key),
            owner=agent,
            timeout_ms=payload.timeout_ms,
        )
    except MemSmithTimeoutError as exc:
        status = runtime.locks.status(runtime.lock_key(agent, key))
        runtime.record_persisted_event(
            "LOCK_TIMEOUT",
            agent=agent,
            key=runtime.lock_key(agent, key),
            value={"held_by": status.held_by, "timeout_ms": payload.timeout_ms},
        )
        raise HTTPException(status_code=408, detail=str(exc)) from exc

    runtime.record_persisted_event(
        "LOCK_ACQUIRE",
        agent=agent,
        key=runtime.lock_key(agent, key),
        value=lock_info.token,
    )
    return asdict(lock_info)


@router.delete("/sessions/{session}/locks/{agent}/{key}")
async def release_lock(session: str, agent: str, key: str, request: Request) -> dict[str, str | None]:
    runtime = _session(request, session)
    runtime.locks.release(runtime.lock_key(agent, key), owner=agent)
    runtime.record_persisted_event("LOCK_RELEASE", agent=agent, key=runtime.lock_key(agent, key))
    return asdict(runtime.locks.status(runtime.lock_key(agent, key)))


@router.get("/sessions/{session}/locks/{key}")
async def lock_status(session: str, key: str, request: Request) -> dict[str, str | None]:
    runtime = _session(request, session)
    return asdict(runtime.locks.status(runtime.lock_key("session", key)))
