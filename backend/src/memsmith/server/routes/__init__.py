"""Explicit route tables for server mode."""

from memsmith.server.routes.health import health_routes
from memsmith.server.routes.sessions import session_routes
from memsmith.server.routes.streams import stream_routes

__all__ = ["health_routes", "session_routes", "stream_routes"]
