from __future__ import annotations

import asyncio
from pathlib import Path

import memsmith


async def researcher(session: object) -> None:
    await session.agent("researcher").push("papers", ["paper-a", "paper-b"])


async def writer(session: object) -> list[str]:
    return await session.agent("writer").wait_for("researcher", "papers")


async def main(*, data_dir: Path | None = None) -> list[str]:
    session = memsmith.session("two-agent-demo", data_dir=data_dir or Path(".memsmith-examples"))
    try:
        writer_task = asyncio.create_task(writer(session))
        await researcher(session)
        return await writer_task
    finally:
        session.close()


if __name__ == "__main__":
    print(asyncio.run(main()))
