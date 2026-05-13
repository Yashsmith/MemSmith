"""Serve command scaffold."""

from __future__ import annotations

import argparse


def add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("serve", help="Start server mode.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7117)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    print(f"memsmith serve scaffold: {args.host}:{args.port}")
    return 0
