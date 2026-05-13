"""Allow `python -m memsmith ...` to execute the CLI."""

from __future__ import annotations

from memsmith.cli.main import main


if __name__ == "__main__":
    raise SystemExit(main())