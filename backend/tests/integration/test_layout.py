from __future__ import annotations

from pathlib import Path


def test_docs_and_examples_exist() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "docs" / "architecture.md").exists()
    assert (root / "docs" / "code-map.md").exists()
    assert (root / "docs" / "contributing.md").exists()
    assert (root / "examples" / "two_agents.py").exists()
    assert (root / "examples" / "crash_recovery.py").exists()
    assert (root / "examples" / "server_mode.py").exists()
    assert (root / "src" / "memsmith" / "__main__.py").exists()
    assert (root / "src" / "memsmith" / "server" / "app.py").exists()
    assert (root / "src" / "memsmith" / "server" / "client.py").exists()
