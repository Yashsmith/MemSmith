"""Thin HTTP client adapter used by `memsmith.connect()`."""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator
from urllib import error, parse, request

from memsmith.errors import MemSmithTimeoutError
from memsmith.observability.history import write_json_history
from memsmith.types import HistoryEvent, LockInfo, StateValue


@dataclass(slots=True)
class RemoteSession:
    """Remote session adapter that preserves the local SDK shape."""

    name: str
    remote_host: str
    transport: str = "remote"
    recovered: bool = False
    _base_url: str = field(init=False)

    def __post_init__(self) -> None:
        if self.remote_host.startswith("http://") or self.remote_host.startswith("https://"):
            self._base_url = self.remote_host.rstrip("/")
        else:
            self._base_url = f"http://{self.remote_host.rstrip('/')}"

    def agent(self, agent_name: str) -> "RemoteAgentContext":
        return RemoteAgentContext(session=self, name=agent_name)

    def state_key(self, agent_name: str, key: str) -> str:
        return f"{agent_name}:{key}"

    def lock_key(self, agent_name: str, key: str) -> str:
        return key

    async def broadcast(self, event: str, *, payload: Any | None = None) -> None:
        await self._request_json(
            "POST",
            f"/sessions/{_quote(self.name)}/broadcast/{_quote(event)}",
            payload={"payload": payload},
        )

    async def checkpoint(self, label: str) -> None:
        await self._request_json("POST", f"/sessions/{_quote(self.name)}/checkpoints/{_quote(label)}")

    async def history(self) -> list[HistoryEvent]:
        payload = await self._request_json("GET", f"/sessions/{_quote(self.name)}/history")
        fields = set(HistoryEvent.__dataclass_fields__.keys())
        return [HistoryEvent(**{key: value for key, value in event.items() if key in fields}) for event in payload["events"]]

    async def export(self, path: str | Path) -> Path:
        events = await self.history()
        return write_json_history(path, events)

    def close(self) -> None:
        return None

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        allow_404: bool = False,
    ) -> dict[str, Any] | None:
        return await asyncio.to_thread(
            self._request_json_sync,
            method,
            path,
            payload,
            allow_404,
        )

    def _request_json_sync(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None,
        allow_404: bool,
    ) -> dict[str, Any] | None:
        url = f"{self._base_url}{path}"
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        req = request.Request(url, data=body, headers=headers, method=method)

        try:
            with request.urlopen(req, timeout=5) as response:
                content = response.read().decode("utf-8")
        except error.HTTPError as exc:
            if allow_404 and exc.code == 404:
                return None
            raise RuntimeError(f"Remote request failed with status {exc.code}: {exc.reason}") from exc

        if not content:
            return {}
        return json.loads(content)


@dataclass(slots=True)
class RemoteAgentContext:
    """Remote agent surface matching the local agent API."""

    session: RemoteSession
    name: str

    async def push(self, key: str, value: Any) -> StateValue:
        payload = await self.session._request_json(
            "POST",
            f"/sessions/{_quote(self.session.name)}/agents/{_quote(self.name)}/state/{_quote(key)}",
            payload={"value": value},
        )
        return StateValue(key=self.session.state_key(self.name, key), value=payload["value"], version=payload["version"])

    async def get(self, key: str) -> Any | None:
        payload = await self.session._request_json(
            "GET",
            f"/sessions/{_quote(self.session.name)}/agents/{_quote(self.name)}/state/{_quote(key)}",
            allow_404=True,
        )
        if payload is None:
            return None
        return payload["value"]

    async def wait_for(
        self,
        source_agent: str,
        key: str,
        after_version: int | None = None,
        timeout_ms: int = 30_000,
    ) -> Any:
        try:
            payload = await self.session._request_json(
                "POST",
                f"/sessions/{_quote(self.session.name)}/agents/{_quote(self.name)}/wait/{_quote(source_agent)}/{_quote(key)}",
                payload={"after_version": after_version, "timeout_ms": timeout_ms},
            )
        except RuntimeError as exc:
            if "408" in str(exc):
                raise MemSmithTimeoutError(str(exc)) from exc
            raise

        return payload["value"]

    @asynccontextmanager
    async def lock(self, key: str, timeout_ms: int = 5_000) -> AsyncIterator[LockInfo]:
        try:
            payload = await self.session._request_json(
                "POST",
                f"/sessions/{_quote(self.session.name)}/locks/{_quote(self.name)}/{_quote(key)}",
                payload={"timeout_ms": timeout_ms},
            )
        except RuntimeError as exc:
            if "408" in str(exc):
                raise MemSmithTimeoutError(str(exc)) from exc
            raise
        lock_info = LockInfo(**payload)
        try:
            yield lock_info
        finally:
            await self.session._request_json(
                "DELETE",
                f"/sessions/{_quote(self.session.name)}/locks/{_quote(self.name)}/{_quote(key)}",
            )

    async def try_lock(self, key: str) -> LockInfo:
        payload = await self.session._request_json(
            "GET",
            f"/sessions/{_quote(self.session.name)}/locks/{_quote(key)}",
        )
        return LockInfo(**payload)


def _quote(value: str) -> str:
    return parse.quote(value, safe="")
