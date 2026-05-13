# Contributing

The first PR path should be obvious.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/unit
pytest tests/integration
pytest tests/smoke
python -m compileall src tests examples
```

Install optional extras only when you are touching those surfaces:

```bash
pip install -e ".[server]"
pip install -e ".[watch]"
```

## Good next contribution areas

- deepen `memsmith watch` into a richer Textual UI on top of `observability/watch.py`
- add remote watch client coverage over the WebSocket endpoint in `server/ws.py`
- turn `cli/commands/serve.py` into a real server launcher over `server/app.py`
- expand integration coverage and examples around the session-backed adapters
- tighten docs and contributor onboarding as the CLI surface grows

## Rules of the repo

- Keep code explicit.
- Avoid framework magic.
- Add tests next to the boundary you changed.
- Update `docs/code-map.md` when a contributor-facing path changes.
- Prefer small, concrete filenames over layered abstractions.
