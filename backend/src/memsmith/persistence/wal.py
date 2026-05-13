"""Write-ahead log scaffolding."""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass, field
from pathlib import Path
from time import time_ns
from typing import Any

import msgspec


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
    """File-backed append-only WAL with a background flush worker.

    The async-facing session code only enqueues entries. A dedicated background
    thread serializes and appends them to disk so local writes can become
    durable without blocking the event loop on file I/O.
    """

    path: Path
    entries: list[WALEntry] = field(default_factory=list)
    _queue: queue.Queue[WALEntry | None] = field(default_factory=queue.Queue, init=False)
    _encoder: msgspec.msgpack.Encoder = field(
        default_factory=msgspec.msgpack.Encoder,
        init=False,
    )
    _decoder: msgspec.msgpack.Decoder = field(
        default_factory=lambda: msgspec.msgpack.Decoder(type=WALEntry),
        init=False,
    )
    _thread: threading.Thread | None = field(default=None, init=False)
    _started: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def start(self) -> None:
        if self._started:
            return

        self._thread = threading.Thread(target=self._flush_worker, daemon=True, name=f"wal:{self.path.name}")
        self._thread.start()
        self._started = True

    def append(self, operation: str, key: str, value: Any, *, version: int) -> WALEntry:
        self.start()
        entry = WALEntry(
            timestamp_ns=time_ns(),
            operation=operation,
            key=key,
            version=version,
            value=value,
        )
        self.entries.append(entry)
        self._queue.put(entry)
        return entry

    def flush(self) -> None:
        if not self._started:
            return
        self._queue.join()

    def close(self) -> None:
        if not self._started:
            return

        self._queue.put(None)
        self._queue.join()
        if self._thread is not None:
            self._thread.join(timeout=1)
        self._started = False
        self._thread = None

    def read_entries(self) -> list[WALEntry]:
        if not self.path.exists():
            return []

        entries: list[WALEntry] = []
        with self.path.open("rb") as handle:
            while True:
                header = handle.read(4)
                if not header:
                    break
                length = int.from_bytes(header, byteorder="big")
                payload = handle.read(length)
                entries.append(self._decoder.decode(payload))
        return entries

    def _flush_worker(self) -> None:
        with self.path.open("ab") as handle:
            while True:
                entry = self._queue.get()
                try:
                    if entry is None:
                        return

                    payload = self._encoder.encode(entry)
                    handle.write(len(payload).to_bytes(4, byteorder="big"))
                    handle.write(payload)
                    handle.flush()
                finally:
                    self._queue.task_done()
