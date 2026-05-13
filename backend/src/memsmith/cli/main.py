"""MemSmith CLI entrypoint."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from memsmith.cli.commands.dump import add_parser as add_dump_parser
from memsmith.cli.commands.serve import add_parser as add_serve_parser
from memsmith.cli.commands.watch import add_parser as add_watch_parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="memsmith")
    subparsers = parser.add_subparsers(dest="command")
    add_dump_parser(subparsers)
    add_serve_parser(subparsers)
    add_watch_parser(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0

    return int(handler(args))
