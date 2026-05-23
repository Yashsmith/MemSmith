from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.Multiagent_test.workflow_benchmark import (
    RESULTS_ROOT,
    has_litellm,
    has_model_matrix_configuration,
    live_suite_skip_reason,
    run_live_suite,
    should_run_live_suite,
)


SKIP_REASON = live_suite_skip_reason()

pytestmark = pytest.mark.skipif(
    bool(SKIP_REASON) or not should_run_live_suite() or not has_litellm() or not has_model_matrix_configuration(),
    reason=SKIP_REASON,
)


def test_three_agent_workflow_compares_memsmith_against_manual_coordination() -> None:
    suite = run_live_suite()
    print(suite["console_report"])

    assert suite["summary"]["all_models_completed"] is True
    assert suite["summary"]["all_memsmith_runs_succeeded"] is True
    assert suite["summary"]["all_memsmith_runs_have_explainability"] is True
    assert suite["summary"]["model_count"] >= 1

    latest_json = RESULTS_ROOT / "latest.json"
    latest_md = RESULTS_ROOT / "latest.md"
    latest_console = RESULTS_ROOT / "latest_console.txt"
    latest_run = RESULTS_ROOT / "latest_run.txt"

    assert latest_json.exists() is True
    assert latest_md.exists() is True
    assert latest_console.exists() is True
    assert latest_run.exists() is True

    latest_payload = json.loads(latest_json.read_text(encoding="utf-8"))
    assert latest_payload["run_id"] == suite["run_id"]

    for comparison in suite["comparisons"]:
        assert comparison["summary"]["memsmith_has_explainability_artifacts"] is True
        assert comparison["with_memsmith"]["success"] is True
        assert comparison["with_memsmith"]["validation"]["resume_matches_final"] is True
        assert comparison["with_memsmith"]["validation"]["watch_contains_wait"] is True
        assert comparison["with_memsmith"]["validation"]["watch_contains_lock"] is True
        assert comparison["with_memsmith"]["quality"]["max_score"] == 100
        assert comparison["without_memsmith"]["quality"]["max_score"] == 100
        assert Path(comparison["with_memsmith"]["artifact_paths"]["dump_text"]).exists() is True
        assert Path(comparison["with_memsmith"]["artifact_paths"]["persisted_watch"]).exists() is True
        assert Path(comparison["without_memsmith"]["artifact_paths"]["manual_trace"]).exists() is True