from __future__ import annotations

import asyncio
import json
from pathlib import Path

import memsmith
from memsmith.cli.main import main


def test_dump_command_prints_persisted_timeline_and_exports_json(tmp_path: Path, capsys) -> None:
    async def scenario() -> None:
        session = memsmith.session("cli-dump", data_dir=tmp_path)
        try:
            await session.agent("researcher").push("papers", ["paper-a"])
            await session.agent("researcher").get("papers")
            await session.agent("writer").wait_for("researcher", "papers")
            async with session.agent("writer").lock("draft"):
                await session.agent("writer").push("draft", "ready")
            await session.broadcast("pipeline_complete")
            await session.checkpoint("after-first")
            session.flush_wal()
        finally:
            session.close()

    asyncio.run(scenario())

    json_out = tmp_path / "dump.json"
    exit_code = main(["dump", "cli-dump", "--data-dir", str(tmp_path), "--json-out", str(json_out)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "MemSmith Session Dump: cli-dump" in captured.out
    assert "SESSION START" in captured.out
    assert "researcher -> PUSH papers" in captured.out
    assert "researcher <- GET researcher:papers" in captured.out
    assert "writer     -> WAIT_FOR researcher:papers" in captured.out
    assert "writer     <- WAIT_FOR_RESOLVE researcher:papers" in captured.out
    assert "writer     -> LOCK_ACQUIRE draft" in captured.out
    assert "SESSION    -> BROADCAST pipeline_complete" in captured.out
    assert "CHECKPOINT -> Saved to" in captured.out

    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload[0]["operation"] == "SESSION_START"
    assert payload[1]["line"].startswith("[00:00.")
