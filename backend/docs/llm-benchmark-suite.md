# LiteLLM Benchmark Suite

This document explains the live benchmark suite under `tests/Multiagent_test/`.

## What it is

The suite runs a real three-agent workflow twice for each configured model:

1. with MemSmith as the coordination layer
2. without MemSmith using plain `asyncio` coordination

It is meant to answer two questions with real provider-backed runs:

- did the workflow complete correctly?
- what extra proof and explainability do we get from MemSmith?

It also records a deterministic quality score so you can see whether the final output
improved, tied, or regressed relative to the manual baseline.

## Why LiteLLM

The suite uses LiteLLM so contributors are not locked into Groq. Any provider that
LiteLLM supports can be used as long as:

- the provider API key is available in the environment or `backend/.env`
- the model string is provided through `MEMSMITH_LITELLM_MODEL` or `MEMSMITH_LITELLM_MODELS`

Examples:

```bash
export MEMSMITH_LITELLM_MODEL="openai/gpt-4.1-mini"
export MEMSMITH_LITELLM_MODEL="anthropic/claude-3-5-haiku-latest"
export MEMSMITH_LITELLM_MODEL="groq/llama-3.3-70b-versatile"
```

For a model matrix:

```bash
export MEMSMITH_LITELLM_MODELS="openai/gpt-4.1-mini,anthropic/claude-3-5-haiku-latest,groq/llama-3.3-70b-versatile"
```

## What it covers

The MemSmith branch of the workflow exercises:

- agent `push()` and `wait_for()` coordination
- lock acquisition and release
- `broadcast()` on completion
- runtime watch streaming
- persisted watch rendering from the WAL
- dump rendering and JSON dump export
- checkpoint creation
- WAL persistence
- `resume()` validation against the final reviewer output

The manual branch exists as a control. It uses `asyncio.Event`, `asyncio.Lock`, a raw
trace log, and a shared dictionary, but it does not produce MemSmith recovery or
explainability artifacts.

## Install

From `backend/`:

```bash
pip install -e ".[dev,llm]"
```

## Configure providers

The suite loads `backend/.env` and exports any missing keys into the process so LiteLLM
can use them. That means contributors can keep provider secrets local without changing
the benchmark code.

Examples of provider keys LiteLLM can use:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GROQ_API_KEY`
- `GEMINI_API_KEY`

The suite does not hardcode any one provider requirement.

## Run

Use `-s` to show the clean console report while pytest runs:

```bash
RUN_LITELLM_MULTIAGENT_SMOKE=1 PYTHONPATH=src ../.venv/bin/python -m pytest tests/Multiagent_test -q -s
```

Optional knobs:

```bash
export MEMSMITH_LITELLM_TEMPERATURE="0.2"
export MEMSMITH_LITELLM_TIMEOUT_S="90"
```

## What the report prints

For every configured model, the suite prints:

- speed and token comparisons for both modes
- deterministic quality scores for both modes
- the final reviewer JSON with MemSmith
- the final reviewer JSON without MemSmith
- the MemSmith runtime watch output
- the MemSmith persisted watch output
- the MemSmith dump output
- the manual baseline trace

This is intended to make a live run readable without opening the artifact directory.

## How quality scoring works

The score is deterministic and scenario-specific. It checks whether the workflow:

- copied the canonical facts exactly
- preserved the required actions
- used the required phase names
- kept the planner grounded in the required fact ids
- carried the primary risk through the plan
- preserved fact traceability in the final output
- mentioned the required quality checks

This is not a universal LLM evaluator. It is a narrow regression tool for this manual
coordination scenario. If both modes score the same, that usually means MemSmith did not
change the final content quality for that run, but it still supplied coordination proof,
recovery artifacts, and explainability.

## What gets written to disk

Every run creates `tests/Multiagent_test/results/<timestamp>/`.

Inside it you will find:

- one subdirectory per model
- `with_memsmith/` artifacts
- `without_memsmith/` artifacts
- per-model `comparison.json` and `comparison.md`
- top-level `suite.json`, `suite.md`, and `console_report.txt`

The `results/` folder also keeps these rolling pointers:

- `latest.json`
- `latest.md`
- `latest_console.txt`
- `latest_run.txt`

## How to interpret the outcome

There are three useful outcomes:

1. MemSmith wins on quality.
2. Both modes tie on quality.
3. The manual baseline wins on quality.

In all three cases, the suite should still show whether MemSmith produced the
explainability and recovery artifacts it promises. That part is the core product proof.

## Recommended contributor workflow

1. Run fast local tests first.
2. Run the live LiteLLM suite on one cheap model.
3. If the change touches prompts or coordination, run the matrix against multiple models.
4. Inspect `latest_console.txt` first, then open the stored run directory if something looks off.