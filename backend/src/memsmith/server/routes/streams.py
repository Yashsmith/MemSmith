"""Streaming route descriptions."""


def stream_routes() -> list[tuple[str, str, str]]:
    return [
        ("GET", "/sessions/{session}/history", "Fetch session history"),
        ("WS", "/sessions/{session}/watch", "Stream watch events"),
    ]
