"""OpenAI Agents SDK integration seam."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from memsmith.session.manager import Session


@dataclass(slots=True)
class MemSmithStore:
    """Optional thin OpenAI Agents-style store over a MemSmith session."""

    session: Session
    agent_name: str = "openai_agents"

    async def set(self, key: str, value: Any) -> None:
        await self.session.agent(self.agent_name).push(key, value)

    async def get(self, key: str) -> Any | None:
        return await self.session.agent(self.agent_name).get(key)
