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