from __future__ import annotations

import asyncio

from examples import server_mode


def test_server_mode_example_uses_real_transport() -> None:
    result = asyncio.run(server_mode.main())
    assert result == "connected"