"""Health and readiness route descriptions."""


def health_routes() -> list[tuple[str, str, str]]:
    return [
        ("GET", "/health", "Process heartbeat"),
        ("GET", "/ready", "Dependency readiness"),
    ]
