from __future__ import annotations

import asyncio
from pathlib import Path

from examples import crash_recovery, two_agents


def test_two_agent_example_runs(tmp_path: Path) -> None:
    result = asyncio.run(two_agents.main(data_dir=tmp_path / "two-agent"))
    assert result == ["paper-a", "paper-b"]


def test_crash_recovery_example_restores_state(tmp_path: Path) -> None:
    result = asyncio.run(crash_recovery.main(data_dir=tmp_path / "recovery"))
    assert result == "checkpointed"
