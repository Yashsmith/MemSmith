from __future__ import annotations

import asyncio

from memsmith.state.shard_store import ShardStore


def test_shard_store_routes_keys_across_real_shards() -> None:
    async def scenario() -> tuple[dict[int, str], list[int], dict[str, int]]:
        store = ShardStore(shards=4)
        keys_by_shard: dict[int, str] = {}

        candidate = 0
        while len(keys_by_shard) < 4 and candidate < 500:
            key = f"key-{candidate}"
            keys_by_shard.setdefault(store.shard_id_for(key), key)
            candidate += 1

        for key in keys_by_shard.values():
            await store.set(key, key)

        snapshot = await store.snapshot()
        versions = {key: snapshot[key].version for key in keys_by_shard.values()}
        return keys_by_shard, store.shard_sizes(), versions

    keys_by_shard, shard_sizes, versions = asyncio.run(scenario())
    assert len(keys_by_shard) >= 2
    assert sum(1 for size in shard_sizes if size > 0) == len(keys_by_shard)
    assert all(version == 1 for version in versions.values())


def test_snapshot_returns_latest_values_and_versions() -> None:
    async def scenario() -> tuple[str, int]:
        store = ShardStore(shards=2)
        await store.set("researcher:papers", ["paper-a"])
        latest = await store.set("researcher:papers", ["paper-a", "paper-b"])
        snapshot = await store.snapshot()
        return snapshot["researcher:papers"].value[1], latest.version

    paper, version = asyncio.run(scenario())
    assert paper == "paper-b"
    assert version == 2