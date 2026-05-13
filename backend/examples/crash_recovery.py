from __future__ import annotations

import asyncio

import memsmith


async def main() -> bool:
    session = memsmith.session("recovery-demo")
    await session.agent("researcher").push("status", "checkpointed")
    await session.checkpoint("after-research")
    recovered = await memsmith.resume("recovery-demo")
    return recovered.recovered


if __name__ == "__main__":
    print(asyncio.run(main()))
