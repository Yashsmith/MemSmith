"""Checkpoint planning helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import time_ns

import msgspec

from memsmith.persistence.paths import session_home
from memsmith.types import StateValue


@dataclass(slots=True, frozen=True)
class CheckpointSnapshot:
    """Serialized checkpoint payload used for recovery."""

    session_name: str
    label: str
    created_at_ns: int
    checkpointed_at_ns: int
    event_count: int
    last_wal_timestamp_ns: int
    states: list[StateValue]


@dataclass(slots=True)
class CheckpointWriter:
    """Resolves checkpoint paths for a session."""

    session_name: str
    base_dir: Path | None = None
    _encoder: msgspec.msgpack.Encoder = field(
        default_factory=msgspec.msgpack.Encoder,
        init=False,
    )
    _decoder: msgspec.msgpack.Decoder = field(
        default_factory=lambda: msgspec.msgpack.Decoder(type=CheckpointSnapshot),
        init=False,
    )

    def path_for(self, label: str) -> Path:
        root = session_home(self.session_name, base_dir=self.base_dir)
        return root / f"{label}.checkpoint"

    def sidecar_path_for(self, label: str) -> Path:
        return self.path_for(label).with_suffix(".checkpoint.json")

    def write(
        self,
        label: str,
        *,
        snapshot: dict[str, StateValue],
        created_at_ns: int,
        event_count: int,
        last_wal_timestamp_ns: int,
    ) -> CheckpointSnapshot:
        payload = CheckpointSnapshot(
            session_name=self.session_name,
            label=label,
            created_at_ns=created_at_ns,
            checkpointed_at_ns=time_ns(),
            event_count=event_count,
            last_wal_timestamp_ns=last_wal_timestamp_ns,
            states=list(snapshot.values()),
        )

        binary_path = self.path_for(label)
        json_path = self.sidecar_path_for(label)
        binary_path.parent.mkdir(parents=True, exist_ok=True)
        binary_path.write_bytes(self._encoder.encode(payload))
        json_path.write_text(json.dumps(asdict(payload), indent=2), encoding="utf-8")
        return payload

    def read(self, path: Path) -> CheckpointSnapshot:
        return self._decoder.decode(path.read_bytes())
