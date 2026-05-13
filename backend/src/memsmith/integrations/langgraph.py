"""LangGraph integration seam."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from memsmith.session.manager import Session


@dataclass(slots=True)
class MemSmithCheckpointer:
    """Thin LangGraph-style checkpointer over a MemSmith session."""

    session: Session
    agent_name: str = "langgraph"

    async def save(self, thread_id: str, value: Any) -> None:
        await self.session.agent(self.agent_name).push(thread_id, value)

    async def load(self, thread_id: str) -> Any | None:
        return await self.session.agent(self.agent_name).get(thread_id)

    async def checkpoint(self, label: str) -> None:
        await self.session.checkpoint(label)
