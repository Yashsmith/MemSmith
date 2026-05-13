from __future__ import annotations

import asyncio
import json
import socket
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from urllib import request

import memsmith
import uvicorn

from memsmith.server.app import create_app


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextmanager
def run_server(*, data_dir: Path) -> str:
    port = _free_port()
    app = create_app(data_dir=data_dir)
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.time() + 5
    while not server.started and time.time() < deadline:
        time.sleep(0.01)

    try:
        yield f"127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=5)


def test_remote_client_push_get_wait_against_running_server(tmp_path: Path) -> None:
    with run_server(data_dir=tmp_path) as host:
        health = json.loads(request.urlopen(f"http://{host}/health", timeout=5).read().decode("utf-8"))
        ready = json.loads(request.urlopen(f"http://{host}/ready", timeout=5).read().decode("utf-8"))

        async def scenario() -> tuple[str | None, str, list[str]]:
            session = await memsmith.connect("remote-demo", host=host)

            async def producer() -> None:
                await asyncio.sleep(0.05)
                await session.agent("researcher").push("status", "ready")

            producer_task = asyncio.create_task(producer())
            resolved = await session.agent("writer").wait_for("researcher", "status", timeout_ms=2_000)
            await producer_task
            current = await session.agent("researcher").get("status")
            history = await session.history()
            return current, resolved, [event.operation for event in history]

        current, resolved, operations = asyncio.run(scenario())

    assert health == {"status": "ok"}
    assert ready == {"status": "ready"}
    assert current == "ready"
    assert resolved == "ready"
    assert "PUSH" in operations
    assert "WAIT_FOR_RESOLVE" in operations