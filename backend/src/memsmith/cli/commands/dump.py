"""Dump command scaffold."""

from __future__ import annotations

import argparse


def add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("dump", help="Dump session history.")
    parser.add_argument("session")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    print(f"memsmith dump scaffold: {args.session}")
    return 0
