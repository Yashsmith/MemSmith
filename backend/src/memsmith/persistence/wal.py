"""Write-ahead log scaffolding."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time_ns
from typing import Any


@dataclass(slots=True, frozen=True)
class WALEntry:
    """Single append-only mutation entry."""

    timestamp_ns: int
    operation: str
    key: str
    version: int
    value: Any


@dataclass(slots=True)
class WAL:
    """Minimal in-memory WAL scaffold.

    This gives contributors an obvious place to add the background thread and
    on-disk append behavior later without hiding the contract.
    """

    entries: list[WALEntry] = field(default_factory=list)

    def append(self, operation: str, key: str, value: Any, *, version: int) -> WALEntry:
        entry = WALEntry(
            timestamp_ns=time_ns(),
            operation=operation,
            key=key,
            version=version,
            value=value,
        )
        self.entries.append(entry)
        return entry
