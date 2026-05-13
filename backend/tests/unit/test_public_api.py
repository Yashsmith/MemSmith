from __future__ import annotations

import asyncio

import memsmith


def test_public_api_exports_top_level_constructors() -> None:
    assert callable(memsmith.session)
    assert callable(memsmith.connect)
    assert callable(memsmith.resume)
    assert memsmith.__version__ == "0.1.0"


def test_session_constructors_expose_transport_and_recovery_state() -> None:
    async def scenario() -> tuple[str, str, bool, str | None]:
        local = memsmith.session("local")
        remote = await memsmith.connect("remote", host="127.0.0.1:7117")
        resumed = await memsmith.resume("recovered")
        return local.transport, remote.transport, resumed.recovered, remote.remote_host

    assert asyncio.run(scenario()) == ("local", "remote", True, "127.0.0.1:7117")
