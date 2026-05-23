# Multiagent Test

This folder contains the opt-in live LiteLLM benchmark suite for MemSmith.

It runs the same three-agent workflow in two modes:

1. with MemSmith coordination
2. without MemSmith using plain `asyncio` events and locks

The suite is skipped by default because it makes real LLM API calls.

## What this suite covers

The MemSmith path validates the surfaces that make the library useful in practice:

- `wait_for()` and lock coordination between agents
- `broadcast()` on workflow completion
- runtime watch output from in-process subscriptions
- persisted watch output from the WAL
- CLI dump output and JSON history export
- checkpoint creation and WAL persistence
- `resume()` correctness against the final reviewer payload
- final-output quality scoring alongside a manual baseline

## Install

From `backend/`:

```bash
pip install -e ".[dev,llm]"
```

## Configure models

Set one or more LiteLLM model strings with either:

```bash
export MEMSMITH_LITELLM_MODEL="groq/llama-3.3-70b-versatile"
```

or a model matrix:

```bash
export MEMSMITH_LITELLM_MODELS="openai/gpt-4.1-mini,anthropic/claude-3-5-haiku-latest,groq/llama-3.3-70b-versatile"
```

Provider API keys can be exported normally or placed in `backend/.env`. The suite
loads `backend/.env` and lets LiteLLM pick up whatever provider keys you configured.

## Run

Use `-s` so the clean report, watch output, dump output, and final payloads are
printed to the terminal while pytest runs.

```bash
RUN_LITELLM_MULTIAGENT_SMOKE=1 PYTHONPATH=src ../.venv/bin/python -m pytest tests/Multiagent_test -q -s
```

## What the output means

Each model gets a side-by-side comparison with:

- duration and token usage for both modes
- deterministic quality scores for both final workflows
- the winning side for speed and quality
- the MemSmith runtime watch, persisted watch, and dump output
- the final reviewer JSON from both modes
- the raw manual trace from the non-MemSmith baseline

The quality score is deterministic and grounded in the scenario requirements. It is
there to show whether MemSmith improved the workflow output for that run, tied it,
or made no measurable difference. MemSmith's main value proposition in this suite is
usually explainability, recovery, and coordination proof, not guaranteed model-score gain.

## What gets stored

Each run writes a timestamped folder under `tests/Multiagent_test/results/` with:

- one subfolder per model in the matrix
- `with_memsmith/` artifacts: runtime watch, persisted watch, dump, history export, snapshot, transcript, checkpoint, WAL
- `without_memsmith/` artifacts: transcript, manual trace, shared state
- per-model `comparison.json` and `comparison.md`
- top-level `suite.json`, `suite.md`, `console_report.txt`
- `latest.json`, `latest.md`, `latest_console.txt`, and `latest_run.txt` pointers

For a full guide, see `docs/llm-benchmark-suite.md`.