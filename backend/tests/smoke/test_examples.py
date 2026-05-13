from __future__ import annotations

import asyncio

from examples import crash_recovery, two_agents


def test_two_agent_example_runs() -> None:
    result = asyncio.run(two_agents.main())
    assert result == ["paper-a", "paper-b"]


def test_crash_recovery_example_restores_state() -> None:
    result = asyncio.run(crash_recovery.main())
    assert result == "checkpointed"
