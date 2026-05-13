"""In-memory shared state store.

The first scaffold intentionally keeps storage obvious. When real sharding lands,
contributors should still be able to open this file and understand the storage
contract without hunting through the rest of the codebase.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from memsmith.types import StateValue


@dataclass(slots=True)
class ShardStore:
    """Versioned in-memory state keyed by `agent:key`."""

    shards: int = 16
    _shards: list[dict[str, StateValue]] = field(default_factory=list, init=False)
    _versions: list[dict[str, int]] = field(default_factory=list, init=False)
    _locks: list[asyncio.Lock] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self._shards = [{} for _ in range(self.shards)]
        self._versions = [{} for _ in range(self.shards)]
        self._locks = [asyncio.Lock() for _ in range(self.shards)]

    def shard_id_for(self, key: str) -> int:
        return hash(key) % self.shards

    def shard_sizes(self) -> list[int]:
        return [len(shard) for shard in self._shards]

    def get(self, key: str) -> StateValue | None:
        shard_id = self.shard_id_for(key)
        return self._shards[shard_id].get(key)

    def version(self, key: str) -> int:
        shard_id = self.shard_id_for(key)
        return self._versions[shard_id].get(key, 0)

    async def set(self, key: str, value: Any) -> StateValue:
        shard_id = self.shard_id_for(key)
        async with self._locks[shard_id]:
            version = self._versions[shard_id].get(key, 0) + 1
            state = StateValue(key=key, value=value, version=version)
            self._shards[shard_id][key] = state
            self._versions[shard_id][key] = version
            return state

    async def snapshot(self) -> dict[str, StateValue]:
        for lock in self._locks:
            await lock.acquire()

        try:
            snapshot: dict[str, StateValue] = {}
            for shard in self._shards:
                snapshot.update(shard)
            return snapshot
        finally:
            for lock in reversed(self._locks):
                lock.release()

    async def put_state(self, state: StateValue) -> None:
        shard_id = self.shard_id_for(state.key)
        async with self._locks[shard_id]:
            self._shards[shard_id][state.key] = state
            self._versions[shard_id][state.key] = state.version

    async def restore(self, snapshot: dict[str, StateValue]) -> None:
        for lock in self._locks:
            await lock.acquire()

        try:
            for shard in self._shards:
                shard.clear()
            for versions in self._versions:
                versions.clear()

            for state in snapshot.values():
                shard_id = self.shard_id_for(state.key)
                self._shards[shard_id][state.key] = state
                self._versions[shard_id][state.key] = state.version
        finally:
            for lock in reversed(self._locks):
                lock.release()
