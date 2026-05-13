"""Explicit lock registry used by the agent API."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from memsmith.errors import LockConflictError, MemSmithTimeoutError
from memsmith.types import LockInfo


@dataclass(slots=True)
class LockRegistry:
    """Owns per-key async locks and current owners."""

    _locks: dict[str, asyncio.Lock] = field(default_factory=dict, init=False)
    _owners: dict[str, str] = field(default_factory=dict, init=False)
    _counts: dict[str, int] = field(default_factory=dict, init=False)

    def _lock(self, key: str) -> asyncio.Lock:
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock

    async def acquire(self, key: str, *, owner: str, timeout_ms: int) -> LockInfo:
        current = self._owners.get(key)
        if current == owner:
            self._counts[key] = self._counts.get(key, 1) + 1
            return LockInfo(key=key, held_by=owner, token=f"{owner}:{key}")

        lock = self._lock(key)
        try:
            await asyncio.wait_for(lock.acquire(), timeout=timeout_ms / 1000)
        except TimeoutError as exc:
            held_by = self._owners.get(key)
            message = f"Timed out acquiring lock for '{key}'."
            if held_by is not None:
                message = f"Timed out acquiring lock for '{key}'; held by '{held_by}'."
            raise MemSmithTimeoutError(message) from exc

        self._owners[key] = owner
        self._counts[key] = 1
        return LockInfo(key=key, held_by=owner, token=f"{owner}:{key}")

    def release(self, key: str, *, owner: str) -> None:
        current = self._owners.get(key)
        if current != owner:
            return

        count = self._counts.get(key, 0)
        if count > 1:
            self._counts[key] = count - 1
            return

        lock = self._lock(key)
        if lock.locked():
            lock.release()
        self._owners.pop(key, None)
        self._counts.pop(key, None)

    def status(self, key: str) -> LockInfo:
        owner = self._owners.get(key)
        token = None if owner is None else f"{owner}:{key}"
        return LockInfo(key=key, held_by=owner, token=token)
