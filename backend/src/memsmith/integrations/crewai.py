"""CrewAI integration seam."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from memsmith.session.manager import Session


@dataclass(slots=True)
class MemSmithMemory:
    """Thin CrewAI-style memory adapter over a MemSmith session."""

    session: Session
    agent_name: str = "crewai"

    async def remember(self, key: str, value: Any) -> None:
        await self.session.agent(self.agent_name).push(key, value)

    async def recall(self, key: str) -> Any | None:
        return await self.session.agent(self.agent_name).get(key)

    async def checkpoint(self, label: str) -> None:
        await self.session.checkpoint(label)
