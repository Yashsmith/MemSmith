"""Agent-scoped API surface."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, AsyncIterator

from memsmith.errors import MemSmithTimeoutError
from memsmith.types import LockInfo, StateValue

if TYPE_CHECKING:
    from memsmith.session.manager import Session


@dataclass(slots=True)
class AgentContext:
    """Per-agent handle used by the public SDK."""

    session: Session
    name: str

    async def push(self, key: str, value: Any) -> StateValue:
        full_key = self.session.state_key(self.name, key)
        state = await self.session.store.set(full_key, value)
        self.session.wal.append("PUSH", full_key, value, version=state.version)
        self.session.record_event(
            "PUSH",
            agent=self.name,
            key=full_key,
            version=state.version,
            value=value,
        )
        await self.session.notify(full_key)
        return state

    async def get(self, key: str) -> Any | None:
        full_key = self.session.state_key(self.name, key)
        state = self.session.store.get(full_key)
        if state is None:
            return None
        self.session.record_event(
            "GET",
            agent=self.name,
            key=full_key,
            version=state.version,
            value=state.value,
        )
        return state.value

    async def wait_for(
        self,
        source_agent: str,
        key: str,
        after_version: int | None = None,
        timeout_ms: int = 30_000,
    ) -> Any:
        full_key = self.session.state_key(source_agent, key)
        current = self.session.store.get(full_key)

        if current is not None and (after_version is None or current.version > after_version):
            self.session.record_event(
                "WAIT_FOR_RESOLVE",
                agent=self.name,
                key=full_key,
                version=current.version,
                value=current.value,
            )
            return current.value

        condition = self.session.waiters.for_key(full_key)
        baseline = after_version or 0

        try:
            async with condition:
                await asyncio.wait_for(
                    condition.wait_for(
                        lambda: self.session.store.version(full_key) > baseline
                    ),
                    timeout=timeout_ms / 1000,
                )
        except TimeoutError as exc:
            raise MemSmithTimeoutError(
                f"Timed out waiting for agent '{source_agent}' to push '{key}'."
            ) from exc

        result = self.session.store.get(full_key)
        if result is None:
            raise MemSmithTimeoutError(
                f"Agent '{source_agent}' notified waiters for '{key}' without storing data."
            )

        self.session.record_event(
            "WAIT_FOR_RESOLVE",
            agent=self.name,
            key=full_key,
            version=result.version,
            value=result.value,
        )
        return result.value

    @asynccontextmanager
    async def lock(self, key: str, timeout_ms: int = 5_000) -> AsyncIterator[LockInfo]:
        full_key = self.session.lock_key(self.name, key)
        lock_info = await self.session.locks.acquire(full_key, owner=self.name, timeout_ms=timeout_ms)
        self.session.record_event("LOCK_ACQUIRE", agent=self.name, key=full_key, value=lock_info.token)
        try:
            yield lock_info
        finally:
            self.session.locks.release(full_key, owner=self.name)
            self.session.record_event("LOCK_RELEASE", agent=self.name, key=full_key)

    async def try_lock(self, key: str) -> LockInfo:
        full_key = self.session.lock_key(self.name, key)
        return self.session.locks.status(full_key)
