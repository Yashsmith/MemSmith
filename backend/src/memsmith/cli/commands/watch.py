"""Watch command scaffold."""

from __future__ import annotations

import argparse


def add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("watch", help="Watch a MemSmith session.")
    parser.add_argument("session")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    print(f"memsmith watch scaffold: {args.session}")
    return 0
