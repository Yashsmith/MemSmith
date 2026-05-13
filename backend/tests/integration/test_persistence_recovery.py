from __future__ import annotations

import asyncio
from pathlib import Path

import memsmith


def test_checkpoint_and_resume_restore_latest_state(tmp_path: Path) -> None:
    async def scenario() -> tuple[list[str], int, bool, bool, bool]:
        session = memsmith.session("recoverable", data_dir=tmp_path)
        try:
            await session.agent("researcher").push("papers", ["paper-a"])
            await session.checkpoint("after-first")
            await session.agent("researcher").push("papers", ["paper-a", "paper-b"])
            session.flush_wal()
        finally:
            session.close()

        recovered = await memsmith.resume("recoverable", data_dir=tmp_path)
        try:
            papers = await recovered.agent("researcher").get("papers")
            version = recovered.store.version("researcher:papers")
        finally:
            recovered.close()

        checkpoint_path = tmp_path / "recoverable" / "after-first.checkpoint"
        sidecar_path = tmp_path / "recoverable" / "after-first.checkpoint.json"
        return papers, version, checkpoint_path.exists(), sidecar_path.exists(), recovered.recovered

    papers, version, checkpoint_exists, sidecar_exists, recovered_flag = asyncio.run(scenario())
    assert papers == ["paper-a", "paper-b"]
    assert version == 2
    assert checkpoint_exists is True
    assert sidecar_exists is True
    assert recovered_flag is True