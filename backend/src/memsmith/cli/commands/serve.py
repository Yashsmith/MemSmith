"""Serve command."""

from __future__ import annotations

import argparse
from pathlib import Path


def add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("serve", help="Start server mode.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7117)
    parser.add_argument("--data-dir", default=None)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    try:
        import uvicorn

        from memsmith.server.app import create_app
    except ImportError as exc:
        print('Server mode requires the optional server dependencies: pip install -e ".[server]"')
        raise SystemExit(1) from exc

    data_dir = Path(args.data_dir) if args.data_dir else None
    app = create_app(data_dir=data_dir)
    print(f"memsmith serve listening on {args.host}:{args.port}", flush=True)
    server = uvicorn.Server(
        uvicorn.Config(app, host=args.host, port=args.port, log_level="info")
    )
    return 0 if server.run() is None else 0
