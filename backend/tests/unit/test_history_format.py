from __future__ import annotations

from memsmith.observability.history import format_event, render_dump
from memsmith.types import HistoryEvent


def test_format_event_renders_relative_timestamp_and_preview() -> None:
    event = HistoryEvent(
        timestamp_ns=1_012_000_000,
        operation="PUSH",
        agent="researcher",
        key="papers",
        version=1,
        value_preview="['paper-a']",
        value_size_bytes=11,
    )

    line = format_event(event, session_start_ns=1_000_000_000)
    assert line == "[00:00.012] researcher -> PUSH papers v1 ['paper-a'] (11b)"


def test_render_dump_includes_header_footer_and_checkpoint_line() -> None:
    events = [
        HistoryEvent(
            timestamp_ns=1_000_000_000,
            operation="SESSION_START",
            agent="session",
            key="demo",
        ),
        HistoryEvent(
            timestamp_ns=2_500_000_000,
            operation="CHECKPOINT",
            agent="session",
            key="/tmp/demo.checkpoint",
            value_preview="/tmp/demo.checkpoint",
        ),
    ]

    rendered = render_dump("demo", events)
    assert "MemSmith Session Dump: demo" in rendered
    assert "[00:01.500] CHECKPOINT -> Saved to /tmp/demo.checkpoint" in rendered
    assert "Total events: 1" in rendered


def test_format_event_renders_coordination_events_with_direction() -> None:
    start = 1_000_000_000
    events = [
        HistoryEvent(
            timestamp_ns=start + 10_000_000,
            operation="WAIT_FOR",
            agent="writer",
            key="researcher:papers",
            value_preview="{'timeout_ms': 30000}",
            value_size_bytes=21,
        ),
        HistoryEvent(
            timestamp_ns=start + 20_000_000,
            operation="WAIT_FOR_RESOLVE",
            agent="writer",
            key="researcher:papers",
            version=2,
            value_preview="['paper-a']",
            value_size_bytes=11,
        ),
        HistoryEvent(
            timestamp_ns=start + 30_000_000,
            operation="LOCK_TIMEOUT",
            agent="editor",
            key="draft",
            value_preview="{'held_by': 'writer'}",
            value_size_bytes=21,
        ),
        HistoryEvent(
            timestamp_ns=start + 40_000_000,
            operation="BROADCAST",
            agent="session",
            key="pipeline_complete",
        ),
    ]

    lines = [format_event(event, session_start_ns=start) for event in events]

    assert lines[0] == "[00:00.010] writer     -> WAIT_FOR researcher:papers {'timeout_ms': 30000} (21b)"
    assert lines[1] == "[00:00.020] writer     <- WAIT_FOR_RESOLVE researcher:papers v2 ['paper-a'] (11b)"
    assert lines[2] == "[00:00.030] editor     !! LOCK_TIMEOUT draft {'held_by': 'writer'} (21b)"
    assert lines[3] == "[00:00.040] SESSION    -> BROADCAST pipeline_complete"
