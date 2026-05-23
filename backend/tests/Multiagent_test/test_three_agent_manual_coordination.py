from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.Multiagent_test.workflow_benchmark import (
    RESULTS_ROOT,
    has_groq_api_key,
    run_live_benchmark,
    should_run_live_smoke,
)


pytestmark = pytest.mark.skipif(
    not should_run_live_smoke() or not has_groq_api_key(),
    reason=(
        "Opt-in live Groq smoke test. Set RUN_GROQ_MULTIAGENT_SMOKE=1 and provide GROQ_API_KEY "
        "through the environment or backend/.env."
    ),
)


def test_three_agent_workflow_compares_memsmith_against_manual_coordination() -> None:
    comparison = run_live_benchmark()

    assert comparison["summary"]["both_succeeded"] is True
    assert comparison["summary"]["memsmith_has_explainability_artifacts"] is True
    assert comparison["with_memsmith"]["validation"]["resume_matches_final"] is True
    assert comparison["with_memsmith"]["validation"]["watch_contains_wait"] is True
    assert comparison["with_memsmith"]["validation"]["watch_contains_lock"] is True

    latest_json = RESULTS_ROOT / "latest.json"
    latest_md = RESULTS_ROOT / "latest.md"
    latest_run = RESULTS_ROOT / "latest_run.txt"

    assert latest_json.exists() is True
    assert latest_md.exists() is True
    assert latest_run.exists() is True

    latest_payload = json.loads(latest_json.read_text(encoding="utf-8"))
    assert latest_payload["run_id"] == comparison["run_id"]
    assert Path(comparison["with_memsmith"]["artifact_paths"]["dump_text"]).exists() is True
    assert Path(comparison["with_memsmith"]["artifact_paths"]["persisted_watch"]).exists() is True
    assert Path(comparison["without_memsmith"]["artifact_paths"]["manual_trace"]).exists() is True