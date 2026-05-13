from __future__ import annotations

from pathlib import Path


def test_docs_and_examples_exist() -> None:
    root = Path(__file__).resolve().parents[2]
    assert (root / "docs" / "architecture.md").exists()
    assert (root / "examples" / "two_agents.py").exists()
    assert (root / "src" / "memsmith" / "server" / "app.py").exists()
