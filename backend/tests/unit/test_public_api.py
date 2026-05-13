from __future__ import annotations

import memsmith


def test_public_api_exports_top_level_constructors() -> None:
    assert callable(memsmith.session)
    assert callable(memsmith.connect)
    assert callable(memsmith.resume)
    assert memsmith.__version__ == "0.1.0"
