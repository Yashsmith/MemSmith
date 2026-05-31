from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from memsmith.server.app import create_app


def test_remote_watch_websocket_receives_runtime_events(tmp_path: Path) -> None:
    app = create_app(data_dir=tmp_path)

    with TestClient(app) as client:
        with client.websocket_connect("/sessions/remote-watch/watch") as websocket:
            response = client.post(
                "/sessions/remote-watch/agents/researcher/state/status",
                json={"value": "ready"},
            )
            assert response.status_code == 200

            payload = websocket.receive_json()

    assert payload["session_name"] == "remote-watch"
    assert payload["sequence"] == 1
    assert payload["event"]["operation"] == "PUSH"
    assert payload["event"]["agent"] == "researcher"
    assert payload["event"]["key"] == "researcher:status"
    assert payload["event"]["line"].endswith("researcher:status v1 'ready' (7b)")
