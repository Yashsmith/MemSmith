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
pip install -e ".[llm]"
```

Run the live LLM benchmark suite only when you want provider-backed verification:

```bash
RUN_LITELLM_MULTIAGENT_SMOKE=1 MEMSMITH_LITELLM_MODELS="groq/llama-3.3-70b-versatile" PYTHONPATH=src ../.venv/bin/python -m pytest tests/Multiagent_test -q -s
```

That suite prints a clean report to stdout and stores the watch, dump, history,
checkpoint, WAL, and quality-comparison artifacts under `tests/Multiagent_test/results/`.

## Good next contribution areas

- deepen `memsmith watch` into a richer interactive Textual UI on top of the grouped renderer in `observability/watch.py`
- add a public remote watch client or `memsmith watch --host ...` path over the WebSocket endpoint in `server/ws.py`
- expand integration coverage and examples around the lightweight session-backed adapters
- plan semantic TTL as a separate state/persistence/observability change
- expand the live LiteLLM benchmark matrix with more coordination scenarios
- tighten docs and contributor onboarding as the CLI surface grows

## Rules of the repo

- Keep code explicit.
- Avoid framework magic.
- Add tests next to the boundary you changed.
- Update `docs/code-map.md` when a contributor-facing path changes.
- Prefer small, concrete filenames over layered abstractions.
