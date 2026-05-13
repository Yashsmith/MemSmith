from __future__ import annotations

import asyncio

import pytest

import memsmith
from memsmith.errors import MemSmithTimeoutError


def test_try_lock_reports_conflicting_owner() -> None:
    async def scenario() -> str | None:
        session = memsmith.session("lock-status")
        async with session.agent("writer").lock("draft"):
            status = await session.agent("editor").try_lock("draft")
            return status.held_by

    assert asyncio.run(scenario()) == "writer"


def test_lock_waits_for_release_and_then_succeeds() -> None:
    async def scenario() -> tuple[str, str | None]:
        session = memsmith.session("lock-waits")

        async def editor_attempt() -> tuple[str, str | None]:
            async with session.agent("editor").lock("draft", timeout_ms=100):
                status = await session.agent("writer").try_lock("draft")
                return "acquired", status.held_by

        async with session.agent("writer").lock("draft"):
            task = asyncio.create_task(editor_attempt())
            await asyncio.sleep(0.01)

        return await task

    result, held_by = asyncio.run(scenario())
    assert result == "acquired"
    assert held_by == "editor"


def test_lock_times_out_when_another_agent_holds_it() -> None:
    async def scenario() -> None:
        session = memsmith.session("lock-timeout")
        async with session.agent("writer").lock("draft"):
            await session.agent("editor").lock("draft", timeout_ms=10).__aenter__()

    with pytest.raises(MemSmithTimeoutError):
        asyncio.run(scenario())