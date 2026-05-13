from __future__ import annotations

import asyncio

import memsmith


async def main() -> str | None:
    session = await memsmith.connect("remote-demo", host="127.0.0.1:7117")
    await session.agent("researcher").push("status", "connected")
    return await session.agent("researcher").get("status")


if __name__ == "__main__":
    print(asyncio.run(main()))
