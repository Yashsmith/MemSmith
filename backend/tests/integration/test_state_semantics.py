from __future__ import annotations

import asyncio

import memsmith


def test_session_waits_and_snapshot_reflect_current_state() -> None:
    async def scenario() -> tuple[list[str], str, dict[str, object], list[int]]:
        session = memsmith.session("state-semantics")

        await asyncio.gather(
            session.agent("researcher").push("papers", ["paper-a", "paper-b"]),
            session.agent("writer").push("draft", "draft-v1"),
        )

        papers = await session.agent("editor").wait_for("researcher", "papers")
        snapshot = await session.snapshot_state()
        return (
            papers,
            snapshot["writer:draft"].value,
            {key: value.version for key, value in snapshot.items()},
            session.store.shard_sizes(),
        )

    papers, draft, versions, shard_sizes = asyncio.run(scenario())
    assert papers == ["paper-a", "paper-b"]
    assert draft == "draft-v1"
    assert versions["researcher:papers"] == 1
    assert versions["writer:draft"] == 1
    assert sum(shard_sizes) == 2