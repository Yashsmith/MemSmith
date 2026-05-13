from __future__ import annotations

import asyncio
import socket
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import memsmith
import uvicorn

from memsmith.server.app import create_app


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextmanager
def run_demo_server(*, data_dir: Path) -> str:
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


async def main() -> str | None:
    with run_demo_server(data_dir=Path(".memsmith-examples")) as host:
        session = await memsmith.connect("remote-demo", host=host)
        await session.agent("researcher").push("status", "connected")
        return await session.agent("researcher").get("status")


if __name__ == "__main__":
    print(asyncio.run(main()))
