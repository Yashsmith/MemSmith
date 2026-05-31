"""History formatting helpers."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from memsmith.persistence.checkpoint import CheckpointWriter
from memsmith.persistence.recovery import build_recovery_plan
from memsmith.persistence.wal import WAL, WALEntry
from memsmith.types import HistoryEvent


def format_event(event: HistoryEvent, *, session_start_ns: int) -> str:
    """Render a single history event in a dump-friendly format."""
    elapsed = _format_elapsed(event.timestamp_ns - session_start_ns)

    if event.operation == "SESSION_START":
        return f"[{elapsed}] SESSION START"

    if event.operation == "CHECKPOINT":
        destination = event.value_preview or event.key
        return f"[{elapsed}] CHECKPOINT -> Saved to {destination}"

    actor = "SESSION" if event.agent == "session" else event.agent
    suffix = _format_suffix(event)

    if event.operation == "GET":
        version = f" v{event.version}" if event.version else ""
        return f"[{elapsed}] {actor:<10} <- GET {event.key}{version}{suffix}".rstrip()

    if event.operation == "WAIT_FOR":
        return f"[{elapsed}] {actor:<10} -> WAIT_FOR {event.key}{suffix}".rstrip()

    if event.operation == "WAIT_FOR_RESOLVE":
        version = f" v{event.version}" if event.version else ""
        return f"[{elapsed}] {actor:<10} <- WAIT_FOR_RESOLVE {event.key}{version}{suffix}".rstrip()

    if event.operation == "WAIT_FOR_TIMEOUT":
        return f"[{elapsed}] {actor:<10} !! WAIT_FOR_TIMEOUT {event.key}{suffix}".rstrip()

    if event.operation == "LOCK_ACQUIRE":
        return f"[{elapsed}] {actor:<10} -> LOCK_ACQUIRE {event.key}{suffix}".rstrip()

    if event.operation == "LOCK_RELEASE":
        return f"[{elapsed}] {actor:<10} -> LOCK_RELEASE {event.key}".rstrip()

    if event.operation == "LOCK_TIMEOUT":
        return f"[{elapsed}] {actor:<10} !! LOCK_TIMEOUT {event.key}{suffix}".rstrip()

    if event.operation == "BROADCAST":
        return f"[{elapsed}] {actor:<10} -> BROADCAST {event.key}{suffix}".rstrip()

    version = f" v{event.version}" if event.version else ""
    return f"[{elapsed}] {actor:<10} -> {event.operation} {event.key}{version}{suffix}".rstrip()


def serialize_event(event: HistoryEvent, *, session_start_ns: int) -> dict[str, Any]:
    payload = asdict(event)
    payload["line"] = format_event(event, session_start_ns=session_start_ns)
    return payload


def serialize_history(events: list[HistoryEvent]) -> list[dict[str, Any]]:
    if not events:
        return []

    session_start_ns = min(event.timestamp_ns for event in events)
    return [serialize_event(event, session_start_ns=session_start_ns) for event in events]


def render_dump(session_name: str, events: list[HistoryEvent]) -> str:
    generated_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    if events:
        session_start_ns = min(event.timestamp_ns for event in events)
        body = [format_event(event, session_start_ns=session_start_ns) for event in events]
        real_events = [event for event in events if event.operation != "SESSION_START"]
        duration_ns = max(event.timestamp_ns for event in events) - session_start_ns
        peak_bytes = max((event.value_size_bytes for event in real_events), default=0)
    else:
        body = ["[00:00.000] SESSION START"]
        real_events = []
        duration_ns = 0
        peak_bytes = 0

    separator = "-" * 41
    footer = (
        f"Total events: {len(real_events)}  |  Duration: {_format_duration(duration_ns)}"
        f"  |  Peak value size: {_format_bytes(peak_bytes)}"
    )
    return "\n".join(
        [
            f"MemSmith Session Dump: {session_name}",
            f"Generated: {generated_at}",
            separator,
            *body,
            separator,
            footer,
        ]
    )


def write_json_history(path: str | Path, events: list[HistoryEvent]) -> Path:
    output_path = Path(path)
    output_path.write_text(json.dumps(serialize_history(events), indent=2), encoding="utf-8")
    return output_path


def load_persisted_history(session_name: str, *, data_dir: str | Path | None = None) -> list[HistoryEvent]:
    base_dir = Path(data_dir) if data_dir is not None else None
    plan = build_recovery_plan(session_name, base_dir=base_dir)
    if plan.checkpoint_path is None and plan.wal_path is None:
        return []

    created_at_ns = None
    if plan.checkpoint_path is not None:
        checkpoint = CheckpointWriter(session_name=session_name, base_dir=base_dir).read(plan.checkpoint_path)
        created_at_ns = checkpoint.created_at_ns

    wal_entries = []
    if plan.wal_path is not None:
        wal_entries = WAL(path=plan.wal_path).read_entries()

    return history_from_wal(session_name, wal_entries, created_at_ns=created_at_ns)


def history_from_wal(
    session_name: str,
    entries: list[WALEntry],
    *,
    created_at_ns: int | None = None,
) -> list[HistoryEvent]:
    if not entries and created_at_ns is None:
        return []

    session_start_ns = created_at_ns if created_at_ns is not None else entries[0].timestamp_ns
    events = [
        HistoryEvent(
            timestamp_ns=session_start_ns,
            operation="SESSION_START",
            agent="session",
            key=session_name,
        )
    ]

    for entry in entries:
        agent, display_key = _display_actor_and_key(entry)
        preview = _preview_from_value(entry.operation, entry.value)
        events.append(
            HistoryEvent(
                timestamp_ns=entry.timestamp_ns,
                operation=entry.operation,
                agent=agent,
                key=display_key,
                version=entry.version,
                value_preview=preview,
                value_size_bytes=_value_size_bytes(entry.value),
            )
        )
    return events


def _display_actor_and_key(entry: WALEntry) -> tuple[str, str]:
    if entry.operation == "PUSH" and ":" in entry.key:
        agent, key = entry.key.split(":", 1)
        return agent, key
    if entry.operation in {
        "GET",
        "WAIT_FOR",
        "WAIT_FOR_RESOLVE",
        "WAIT_FOR_TIMEOUT",
        "LOCK_ACQUIRE",
        "LOCK_RELEASE",
        "LOCK_TIMEOUT",
    } and ":" in entry.key:
        agent, key = entry.key.split(":", 1)
        return agent, key
    if entry.operation == "CHECKPOINT" and isinstance(entry.value, dict):
        return "session", str(entry.value.get("path", entry.key))
    return "session", entry.key


def _preview_from_value(operation: str, value: Any) -> str | None:
    if value is None:
        return None
    if operation == "CHECKPOINT" and isinstance(value, dict):
        path = value.get("path")
        return str(path) if path is not None else None
    return repr(value)[:80]


def _format_elapsed(delta_ns: int) -> str:
    total_ms = max(delta_ns, 0) // 1_000_000
    minutes, remainder_ms = divmod(total_ms, 60_000)
    seconds, milliseconds = divmod(remainder_ms, 1_000)
    return f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def _format_duration(duration_ns: int) -> str:
    return f"{duration_ns / 1_000_000_000:.3f}s"


def _format_bytes(size_bytes: int) -> str:
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f}kb"
    return f"{size_bytes}b"


def _format_suffix(event: HistoryEvent) -> str:
    preview = f" {event.value_preview}" if event.value_preview is not None else ""
    size = f" ({_format_bytes(event.value_size_bytes)})" if event.value_size_bytes else ""
    return f"{preview}{size}"


def _value_size_bytes(value: Any) -> int:
    if value is None:
        return 0
    return len(repr(value).encode("utf-8"))
