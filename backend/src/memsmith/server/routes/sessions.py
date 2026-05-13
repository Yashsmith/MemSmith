"""Session transport route descriptions."""


def session_routes() -> list[tuple[str, str, str]]:
    return [
        ("POST", "/sessions/{session}/agents/{agent}/state/{key}", "Push agent state"),
        ("GET", "/sessions/{session}/agents/{agent}/state/{key}", "Read agent state"),
        ("POST", "/sessions/{session}/broadcast/{event}", "Broadcast session event"),
    ]
