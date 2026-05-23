# Multiagent Test

This folder contains the opt-in live three-agent benchmark that compares:

1. coordination through MemSmith
2. manual coordination without MemSmith

It is intentionally skipped by default because it makes real Groq API calls.

## How to run

From `backend/`:

```bash
RUN_GROQ_MULTIAGENT_SMOKE=1 PYTHONPATH=src python -m pytest tests/Multiagent_test -q
```

The harness looks for `GROQ_API_KEY` in the environment first. If it is not
exported, it will read it from `backend/.env`.

## What it stores

Each live run writes a timestamped folder under `tests/Multiagent_test/results/`
with:

- per-mode LLM transcripts and benchmark summaries
- MemSmith dump/watch/export artifacts
- checkpoint/WAL-backed session data for the MemSmith run
- a comparison JSON and Markdown report
- `latest.json`, `latest.md`, and `latest_run.txt` pointers for the most recent run

The MemSmith mode also verifies resume/recovery and records the explainability
artifacts produced by `memsmith dump` and `memsmith watch`.