from __future__ import annotations

import asyncio

from examples import two_agents


def test_two_agent_example_runs() -> None:
    result = asyncio.run(two_agents.main())
    assert result == ["paper-a", "paper-b"]
