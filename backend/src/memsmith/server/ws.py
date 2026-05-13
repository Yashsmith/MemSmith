"""WebSocket boundary for remote watch mode."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from memsmith.observability.history import serialize_event

def watch_channel_name(session_name: str) -> str:
    return f"memsmith.watch.{session_name}"


router = APIRouter()


@router.websocket("/sessions/{session}/watch")
async def watch_session(websocket: WebSocket, session: str) -> None:
    runtime = websocket.app.state.registry.get(session)
    queue = runtime.subscribe()
    await websocket.accept()

    try:
        while True:
            envelope = await queue.get()
            await websocket.send_json(
                {
                    "session_name": envelope.session_name,
                    "sequence": envelope.sequence,
                    "event": serialize_event(envelope.event, session_start_ns=runtime.created_at_ns),
                }
            )
    except WebSocketDisconnect:
        return
    finally:
        runtime.unsubscribe(queue)
