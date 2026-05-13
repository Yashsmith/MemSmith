from __future__ import annotations

import asyncio
from pathlib import Path

import memsmith
from memsmith.integrations.crewai import MemSmithMemory
from memsmith.integrations.langgraph import MemSmithCheckpointer
from memsmith.integrations.openai_agents import MemSmithStore


def test_integrations_delegate_to_core_session_behaviors(tmp_path: Path) -> None:
    async def scenario() -> tuple[dict[str, str] | None, str | None, dict[str, str] | None, bool]:
        session = memsmith.session("integration-demo", data_dir=tmp_path)
        try:
            checkpointer = MemSmithCheckpointer(session=session)
            memory = MemSmithMemory(session=session)
            store = MemSmithStore(session=session)

            await checkpointer.save("thread-1", {"step": "draft"})
            await memory.remember("summary", "ready")
            await store.set("tool_state", {"status": "cached"})
            await checkpointer.checkpoint("integrations")

            checkpoint_exists = (tmp_path / "integration-demo" / "integrations.checkpoint").exists()
            return (
                await checkpointer.load("thread-1"),
                await memory.recall("summary"),
                await store.get("tool_state"),
                checkpoint_exists,
            )
        finally:
            session.close()

    checkpoint_value, memory_value, store_value, checkpoint_exists = asyncio.run(scenario())
    assert checkpoint_value == {"step": "draft"}
    assert memory_value == "ready"
    assert store_value == {"status": "cached"}
    assert checkpoint_exists is True