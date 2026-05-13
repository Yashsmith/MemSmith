"""In-memory shared state store.

The first scaffold intentionally keeps storage obvious. When real sharding lands,
contributors should still be able to open this file and understand the storage
contract without hunting through the rest of the codebase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from memsmith.types import StateValue


@dataclass(slots=True)
class ShardStore:
    """Versioned in-memory state keyed by `agent:key`."""

    shards: int = 16
    _values: dict[str, StateValue] = field(default_factory=dict, init=False)
    _versions: dict[str, int] = field(default_factory=dict, init=False)

    def get(self, key: str) -> StateValue | None:
        return self._values.get(key)

    def version(self, key: str) -> int:
        return self._versions.get(key, 0)

    def set(self, key: str, value: Any) -> StateValue:
        version = self.version(key) + 1
        state = StateValue(key=key, value=value, version=version)
        self._values[key] = state
        self._versions[key] = version
        return state
