"""Per-key wait primitives for `wait_for`."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field


@dataclass(slots=True)
class WaitRegistry:
    """Creates and caches asyncio conditions by state key."""

    _conditions: dict[str, asyncio.Condition] = field(default_factory=dict, init=False)

    def for_key(self, key: str) -> asyncio.Condition:
        condition = self._conditions.get(key)
        if condition is None:
            condition = asyncio.Condition()
            self._conditions[key] = condition
        return condition
