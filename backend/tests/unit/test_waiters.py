from __future__ import annotations

import asyncio

import pytest

import memsmith
from memsmith.errors import MemSmithTimeoutError


def test_wait_for_returns_existing_value_immediately() -> None:
    async def scenario() -> tuple[list[str], list[str]]:
        session = memsmith.session("wait-existing")
        await session.agent("researcher").push("papers", ["paper-a", "paper-b"])
        result = await session.agent("writer").wait_for("researcher", "papers")
        history = await session.history()
        return result, [event.operation for event in history]

    result, operations = asyncio.run(scenario())
    assert result == ["paper-a", "paper-b"]
    assert operations[-2:] == ["WAIT_FOR", "WAIT_FOR_RESOLVE"]


def test_wait_for_honors_after_version() -> None:
    async def scenario() -> tuple[str, list[str]]:
        session = memsmith.session("wait-after-version")
        initial = await session.agent("researcher").push("status", "draft")
        waiter = asyncio.create_task(
            session.agent("writer").wait_for("researcher", "status", after_version=initial.version)
        )
        await asyncio.sleep(0)
        await session.agent("researcher").push("status", "done")
        result = await waiter
        history = await session.history()
        return result, [event.operation for event in history]

    result, operations = asyncio.run(scenario())
    assert result == "done"
    assert operations == ["PUSH", "WAIT_FOR", "PUSH", "WAIT_FOR_RESOLVE"]


def test_wait_for_times_out_when_value_does_not_arrive() -> None:
    async def scenario() -> None:
        session = memsmith.session("wait-timeout")
        await session.agent("writer").wait_for("researcher", "papers", timeout_ms=10)

    with pytest.raises(MemSmithTimeoutError):
        asyncio.run(scenario())


def test_wait_for_timeout_is_recorded_before_raise() -> None:
    async def scenario() -> list[str]:
        session = memsmith.session("wait-timeout-recorded")
        try:
            await session.agent("writer").wait_for("researcher", "papers", timeout_ms=10)
        except MemSmithTimeoutError:
            history = await session.history()
            return [event.operation for event in history]
        raise AssertionError("wait_for should have timed out")

    assert asyncio.run(scenario()) == ["WAIT_FOR", "WAIT_FOR_TIMEOUT"]
