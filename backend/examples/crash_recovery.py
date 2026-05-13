from __future__ import annotations

import asyncio
from pathlib import Path

import memsmith


async def main(*, data_dir: Path | None = None) -> str | None:
    data_dir = data_dir or Path(".memsmith-examples")
    session = memsmith.session("recovery-demo", data_dir=data_dir)
    try:
        await session.agent("researcher").push("status", "checkpointed")
        await session.checkpoint("after-research")
        recovered = await memsmith.resume("recovery-demo", data_dir=data_dir)
        try:
            return await recovered.agent("researcher").get("status")
        finally:
            recovered.close()
    finally:
        session.close()


if __name__ == "__main__":
    print(asyncio.run(main()))
