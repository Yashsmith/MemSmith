from __future__ import annotations

import asyncio

import memsmith


async def researcher(session: object) -> None:
    await session.agent("researcher").push("papers", ["paper-a", "paper-b"])


async def writer(session: object) -> list[str]:
    return await session.agent("writer").wait_for("researcher", "papers")


async def main() -> list[str]:
    session = memsmith.session("two-agent-demo")
    writer_task = asyncio.create_task(writer(session))
    await researcher(session)
    return await writer_task


if __name__ == "__main__":
    print(asyncio.run(main()))
