from __future__ import annotations

import asyncio

import pytest

import memsmith
from memsmith.errors import MemSmithTimeoutError


def test_wait_for_returns_existing_value_immediately() -> None:
    async def scenario() -> list[str]:
        session = memsmith.session("wait-existing")
        await session.agent("researcher").push("papers", ["paper-a", "paper-b"])
        return await session.agent("writer").wait_for("researcher", "papers")

    assert asyncio.run(scenario()) == ["paper-a", "paper-b"]


def test_wait_for_honors_after_version() -> None:
    async def scenario() -> str:
        session = memsmith.session("wait-after-version")
        initial = await session.agent("researcher").push("status", "draft")
        waiter = asyncio.create_task(
            session.agent("writer").wait_for("researcher", "status", after_version=initial.version)
        )
        await asyncio.sleep(0)
        await session.agent("researcher").push("status", "done")
        return await waiter

    assert asyncio.run(scenario()) == "done"


def test_wait_for_times_out_when_value_does_not_arrive() -> None:
    async def scenario() -> None:
        session = memsmith.session("wait-timeout")
        await session.agent("writer").wait_for("researcher", "papers", timeout_ms=10)

    with pytest.raises(MemSmithTimeoutError):
        asyncio.run(scenario())