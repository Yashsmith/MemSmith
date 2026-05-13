"""FastAPI application for remote MemSmith sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI

from memsmith.session.manager import Session
from memsmith.server.routes.health import router as health_router
from memsmith.server.routes.sessions import router as sessions_router
from memsmith.server.routes.streams import router as streams_router
from memsmith.server.ws import router as watch_router


@dataclass(slots=True)
class SessionRegistry:
    """Keeps one local runtime per session name for server mode."""

    data_dir: Path | None = None
    _sessions: dict[str, Session] = field(default_factory=dict)

    def get(self, session_name: str) -> Session:
        if session_name not in self._sessions:
            self._sessions[session_name] = Session(name=session_name, data_dir=self.data_dir)
        return self._sessions[session_name]


def create_app(*, data_dir: str | Path | None = None) -> FastAPI:
    """Create the MemSmith server app using the local runtime as source of truth."""
    app = FastAPI(title="MemSmith", version="0.1.0")
    app.state.registry = SessionRegistry(data_dir=Path(data_dir) if data_dir else None)
    app.include_router(health_router)
    app.include_router(sessions_router)
    app.include_router(streams_router)
    app.include_router(watch_router)
    return app
