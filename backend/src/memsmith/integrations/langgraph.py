"""LangGraph integration seam."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MemSmithCheckpointer:
    """Placeholder integration object for LangGraph."""

    session_id: str
