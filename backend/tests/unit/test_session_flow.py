from __future__ import annotations

import asyncio
import json

import memsmith


def test_push_and_wait_for_flow() -> None:
    async def scenario() -> str:
        session = memsmith.session("demo")
        await session.agent("researcher").push("papers", ["paper-a"])
        result = await session.agent("writer").wait_for("researcher", "papers")
        return result[0]

    assert asyncio.run(scenario()) == "paper-a"


def test_lock_context_records_history() -> None:
    async def scenario() -> tuple[list[str], list[str]]:
        session = memsmith.session("demo-locks")
        async with session.agent("writer").lock("draft"):
            await session.agent("writer").push("draft", "hello")
        history = await session.history()
        assert all(event.timestamp_ns >= session.created_at_ns for event in history)
        assert session.event_count == len(history)
        return [event.operation for event in history], [event.key for event in history]

    operations, keys = asyncio.run(scenario())
    assert operations[:2] == ["LOCK_ACQUIRE", "PUSH"]
    assert operations[-1] == "LOCK_RELEASE"
    assert keys[0] == "draft"
    assert keys[1] == "writer:draft"


def test_export_includes_timestamped_history(tmp_path) -> None:
    async def scenario() -> dict[str, object]:
        session = memsmith.session("export-history")
        await session.agent("researcher").push("papers", ["paper-a"])
        export_path = await session.export(tmp_path / "history.json")
        return json.loads(export_path.read_text(encoding="utf-8"))[0]

    payload = asyncio.run(scenario())
    assert payload["timestamp_ns"] > 0
    assert payload["operation"] == "PUSH"
    assert payload["agent"] == "researcher"
