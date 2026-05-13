# Contributing

The first PR path should be obvious.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest tests/unit
```

## Good first contribution areas

- tighten state version semantics
- add real sharding behind `state/shard_store.py`
- implement on-disk WAL in `persistence/wal.py`
- build dump formatting in `observability/history.py`
- replace the server scaffold with FastAPI routes in `server/`

## Rules of the repo

- Keep code explicit.
- Avoid framework magic.
- Add tests next to the boundary you changed.
- Update `docs/code-map.md` when a contributor-facing path changes.
- Prefer small, concrete filenames over layered abstractions.
