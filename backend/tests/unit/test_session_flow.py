from __future__ import annotations

import asyncio

import memsmith


def test_push_and_wait_for_flow() -> None:
    async def scenario() -> str:
        session = memsmith.session("demo")
        await session.agent("researcher").push("papers", ["paper-a"])
        result = await session.agent("writer").wait_for("researcher", "papers")
        return result[0]

    assert asyncio.run(scenario()) == "paper-a"


def test_lock_context_records_history() -> None:
    async def scenario() -> list[str]:
        session = memsmith.session("demo-locks")
        async with session.agent("writer").lock("draft"):
            await session.agent("writer").push("draft", "hello")
        history = await session.history()
        return [event.operation for event in history]

    operations = asyncio.run(scenario())
    assert operations[:2] == ["LOCK_ACQUIRE", "PUSH"]
    assert operations[-1] == "LOCK_RELEASE"
