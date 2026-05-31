from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib import request


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_serve_command_starts_health_endpoint(tmp_path: Path) -> None:
    port = _free_port()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "memsmith",
            "serve",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--data-dir",
            str(tmp_path),
        ],
        cwd=Path(__file__).resolve().parents[2],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        deadline = time.time() + 5
        response = None
        while time.time() < deadline:
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout is not None else ""
                raise AssertionError(f"serve process exited early:\n{output}")
            try:
                response = request.urlopen(f"http://127.0.0.1:{port}/health", timeout=0.2)
                break
            except OSError:
                time.sleep(0.05)

        assert response is not None
        assert json.loads(response.read().decode("utf-8")) == {"status": "ok"}
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
