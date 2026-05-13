"""FastAPI route modules for server mode."""

from memsmith.server.routes.health import router as health_router
from memsmith.server.routes.sessions import router as sessions_router
from memsmith.server.routes.streams import router as streams_router

__all__ = ["health_router", "sessions_router", "streams_router"]
