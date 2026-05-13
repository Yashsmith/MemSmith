"""Watch command scaffold."""

from __future__ import annotations

import argparse
import asyncio

from memsmith.observability.watch import PersistedWatchConsumer, render_watch


def add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("watch", help="Watch a MemSmith session.")
    parser.add_argument("session")
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--idle-timeout-ms", type=int, default=2_000)
    parser.add_argument("--poll-interval-ms", type=int, default=50)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    envelopes = asyncio.run(
        PersistedWatchConsumer(session_name=args.session, data_dir=args.data_dir).collect(
            limit=args.limit,
            idle_timeout_ms=args.idle_timeout_ms,
            poll_interval_ms=args.poll_interval_ms,
        )
    )
    print(render_watch(args.session, envelopes))
    return 0
