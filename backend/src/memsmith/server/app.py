"""Server entrypoint scaffold.

This intentionally avoids framework imports so the local package remains easy to
import before optional server dependencies are installed.
"""

from __future__ import annotations

from memsmith.server.routes.health import health_routes
from memsmith.server.routes.sessions import session_routes
from memsmith.server.routes.streams import stream_routes


def create_app() -> dict[str, object]:
    """Return a route description until the FastAPI app lands."""
    return {
        "mode": "server",
        "routes": [*health_routes(), *session_routes(), *stream_routes()],
    }
