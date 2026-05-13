"""Dump command scaffold."""

from __future__ import annotations

import argparse
from pathlib import Path

from memsmith.observability.history import load_persisted_history, render_dump, write_json_history


def add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("dump", help="Dump session history.")
    parser.add_argument("session")
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--json-out", default=None)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    events = load_persisted_history(args.session, data_dir=args.data_dir)
    if not events:
        print(f"No persisted history found for session '{args.session}'.")
        return 1

    if args.json_out:
        write_json_history(Path(args.json_out), events)

    print(render_dump(args.session, events))
    return 0
