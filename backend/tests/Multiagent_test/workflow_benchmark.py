"""LiteLLM-backed multi-model benchmark suite for MemSmith coordination."""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import io
import json
import os
import re
import shutil
from contextlib import redirect_stdout
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import memsmith
from memsmith.cli.main import main as memsmith_cli_main
from memsmith.observability.watch import render_watch, subscribe

BACKEND_ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = Path(__file__).resolve().parent / "results"
RUN_OPT_IN_ENV = "RUN_LITELLM_MULTIAGENT_SMOKE"
MODEL_MATRIX_ENV = "MEMSMITH_LITELLM_MODELS"
DEFAULT_MODEL_ENV = "MEMSMITH_LITELLM_MODEL"
TEMPERATURE_ENV = "MEMSMITH_LITELLM_TEMPERATURE"
TIMEOUT_ENV = "MEMSMITH_LITELLM_TIMEOUT_S"

DEFAULT_TEMPERATURE = 0.2
DEFAULT_TIMEOUT_S = 90.0
AUTO_MODEL_FALLBACKS = (("GROQ_API_KEY", "groq/llama-3.3-70b-versatile"),)
SECTION_RULE = "=" * 88
SUBSECTION_RULE = "-" * 88

SCENARIO_NAME = "atlas_launch_manual"
SCENARIO_BRIEF = """
You are coordinating a launch-readiness workflow for Atlas Notes.

Source packet:
- product_name: Atlas Notes
- launch_date: 2026-09-15
- budget_cap: $25,000
- team_shape: 2 engineers and 1 designer for 6 weeks
- target_metric: 150 design partners in pilot
- success_metric: 80% weekly active usage after 30 days
- hard_requirement: SOC2-ready logging before pilot
- primary_risk: data import errors during onboarding
- must_have_actions: onboarding docs, rollback drill, customer feedback loop

The goal is to deliver a launch brief that is accurate, structured, and fully grounded in the source packet.
""".strip()

CANONICAL_FACTS = {
    "product_name": "Atlas Notes",
    "launch_date": "2026-09-15",
    "budget_cap": "$25,000",
    "team_shape": "2 engineers and 1 designer for 6 weeks",
    "target_metric": "150 design partners in pilot",
    "success_metric": "80% weekly active usage after 30 days",
    "hard_requirement": "SOC2-ready logging before pilot",
    "primary_risk": "data import errors during onboarding",
}
MUST_HAVE_ACTIONS = ["onboarding docs", "rollback drill", "customer feedback loop"]
PHASE_NAMES = ["prep", "pilot", "launch"]


@dataclass(slots=True)
class ModeArtifacts:
    mode: str
    root: Path
    files: dict[str, str] = field(default_factory=dict)

    def record(self, key: str, path: Path) -> None:
        self.files[key] = str(path)


@dataclass(slots=True)
class ModeRunResult:
    mode: str
    success: bool
    duration_s: float
    llm_calls: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    validation: dict[str, Any]
    quality: dict[str, Any]
    artifact_paths: dict[str, str]
    workflow_outputs: dict[str, Any]
    coordination_events: int
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ManualCoordinator:
    values: dict[str, Any] = field(default_factory=dict)
    versions: dict[str, int] = field(default_factory=dict)
    trace: list[dict[str, Any]] = field(default_factory=list)
    _events: dict[str, asyncio.Event] = field(default_factory=dict)

    def _event_for(self, full_key: str) -> asyncio.Event:
        event = self._events.get(full_key)
        if event is None:
            event = asyncio.Event()
            self._events[full_key] = event
        return event

    async def push(self, agent: str, key: str, value: Any) -> int:
        full_key = f"{agent}:{key}"
        version = self.versions.get(full_key, 0) + 1
        self.values[full_key] = value
        self.versions[full_key] = version
        self.trace.append(
            {
                "agent": agent,
                "operation": "PUSH",
                "key": full_key,
                "version": version,
                "value": value,
            }
        )
        self._event_for(full_key).set()
        return version

    async def wait_for(self, agent: str, source_agent: str, key: str, *, timeout_ms: int = 30_000) -> Any:
        full_key = f"{source_agent}:{key}"
        if full_key not in self.values:
            await asyncio.wait_for(self._event_for(full_key).wait(), timeout=timeout_ms / 1000)
        value = self.values[full_key]
        self.trace.append(
            {
                "agent": agent,
                "operation": "WAIT_FOR_RESOLVE",
                "key": full_key,
                "version": self.versions[full_key],
                "value": value,
            }
        )
        return value


class LiteLLMChatClient:
    """Small wrapper around LiteLLM so the suite stays provider-agnostic."""

    def __init__(
        self,
        model: str,
        *,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> None:
        self.model = model
        self._timeout_s = timeout_s
        self._temperature = temperature
        self._litellm: Any | None = None

    def _module(self) -> Any:
        if self._litellm is None:
            self._litellm = importlib.import_module("litellm")
            if hasattr(self._litellm, "drop_params"):
                self._litellm.drop_params = True
        return self._litellm

    async def complete_json(
        self,
        *,
        mode: str,
        agent: str,
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        litellm = self._module()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        last_error: Exception | None = None
        for attempt in range(1, 4):
            started_at = perf_counter()
            try:
                response = await litellm.acompletion(
                    model=self.model,
                    messages=messages,
                    temperature=self._temperature,
                    timeout=self._timeout_s,
                )
                content = _extract_message_content(response)
                parsed = _extract_json_object(content)
            except Exception as exc:  # pragma: no cover - exercised by opt-in live runs only
                last_error = exc
                if attempt == 3:
                    raise RuntimeError(
                        f"LiteLLM completion failed for {mode}/{agent}/{self.model}: {exc}"
                    ) from exc
                continue

            latency_s = perf_counter() - started_at
            usage = _extract_usage(response)
            transcript = {
                "mode": mode,
                "agent": agent,
                "attempt": attempt,
                "model": str(_get_value(response, "model", self.model)),
                "latency_s": round(latency_s, 4),
                "prompt_tokens": usage["prompt_tokens"],
                "completion_tokens": usage["completion_tokens"],
                "total_tokens": usage["total_tokens"],
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response": parsed,
            }
            return parsed, transcript

        raise RuntimeError(f"LiteLLM completion failed for {mode}/{agent}/{self.model}: {last_error}")


def should_run_live_suite() -> bool:
    return _truthy(os.getenv(RUN_OPT_IN_ENV, ""))


def has_litellm() -> bool:
    return importlib.util.find_spec("litellm") is not None


def has_model_matrix_configuration() -> bool:
    return bool(resolve_model_matrix())


def live_suite_skip_reason() -> str:
    reasons: list[str] = []
    if not should_run_live_suite():
        reasons.append(f"Set {RUN_OPT_IN_ENV}=1 to opt into live provider-backed tests.")
    if not has_litellm():
        reasons.append('Install LiteLLM first with `pip install -e ".[llm]"` or `pip install litellm`.')
    if not has_model_matrix_configuration():
        reasons.append(
            f"Configure at least one model with {MODEL_MATRIX_ENV} or {DEFAULT_MODEL_ENV}; provider keys may live in backend/.env."
        )
    return " ".join(reasons)


def resolve_model_matrix() -> list[str]:
    _load_backend_env()

    configured = os.getenv(MODEL_MATRIX_ENV) or os.getenv(DEFAULT_MODEL_ENV)
    models = _parse_model_list(configured or "")
    if models:
        return models

    for env_key, fallback_model in AUTO_MODEL_FALLBACKS:
        if os.getenv(env_key):
            return [fallback_model]
    return []


def run_live_suite() -> dict[str, Any]:
    models = resolve_model_matrix()
    if not models:
        raise RuntimeError(
            f"No LiteLLM models configured. Set {MODEL_MATRIX_ENV} or {DEFAULT_MODEL_ENV}."
        )
    return asyncio.run(_run_live_suite(models))


async def _run_live_suite(models: list[str]) -> dict[str, Any]:
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    run_dir = RESULTS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    suite_result: dict[str, Any] = {
        "run_id": run_id,
        "suite": "litellm_multiagent_matrix",
        "scenario": SCENARIO_NAME,
        "generated_at": datetime.now().astimezone().isoformat(),
        "models_requested": models,
    }

    comparisons: list[dict[str, Any]] = []
    try:
        for model in models:
            client = LiteLLMChatClient(
                model,
                timeout_s=_float_env(TIMEOUT_ENV, DEFAULT_TIMEOUT_S),
                temperature=_float_env(TEMPERATURE_ENV, DEFAULT_TEMPERATURE),
            )
            comparison = await _run_model_comparison(client, run_dir / _slugify(model))
            comparisons.append(comparison)

        suite_result["comparisons"] = comparisons
        suite_result["summary"] = _build_suite_summary(comparisons)

        _write_json(run_dir / "suite.json", suite_result)
        (run_dir / "suite.md").write_text(_render_suite_markdown(suite_result), encoding="utf-8")
        console_report = _render_console_report(suite_result)
        (run_dir / "console_report.txt").write_text(console_report, encoding="utf-8")
        _update_latest(run_dir)

        suite_result["artifacts"] = {
            "suite_json": str(run_dir / "suite.json"),
            "suite_markdown": str(run_dir / "suite.md"),
            "console_report": str(run_dir / "console_report.txt"),
        }
        suite_result["console_report"] = console_report
        return suite_result
    except Exception as exc:
        suite_result["comparisons"] = comparisons
        suite_result["error"] = str(exc)
        _write_json(run_dir / "suite.failure.json", suite_result)
        (run_dir / "console_report.failure.txt").write_text(
            _render_failure_console_report(suite_result),
            encoding="utf-8",
        )
        _update_latest(run_dir)
        raise


async def _run_model_comparison(client: LiteLLMChatClient, model_dir: Path) -> dict[str, Any]:
    model_dir.mkdir(parents=True, exist_ok=True)
    with_memsmith = await _run_with_memsmith(client, model_dir / "with_memsmith")
    without_memsmith = await _run_without_memsmith(client, model_dir / "without_memsmith")

    comparison = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "model": client.model,
        "model_slug": model_dir.name,
        "artifacts_root": str(model_dir),
        "with_memsmith": asdict(with_memsmith),
        "without_memsmith": asdict(without_memsmith),
        "summary": _build_comparison_summary(with_memsmith, without_memsmith),
    }
    _write_json(model_dir / "comparison.json", comparison)
    (model_dir / "comparison.md").write_text(
        _render_model_markdown_report(comparison),
        encoding="utf-8",
    )
    return comparison


async def _run_with_memsmith(client: LiteLLMChatClient, mode_dir: Path) -> ModeRunResult:
    mode_dir.mkdir(parents=True, exist_ok=True)
    artifacts = ModeArtifacts(mode="with_memsmith", root=mode_dir)
    transcripts: list[dict[str, Any]] = []
    session_name = f"multiagent-benchmark-{datetime.now().astimezone().strftime('%H%M%S')}"
    data_dir = mode_dir / "state"
    session = memsmith.session(session_name, data_dir=data_dir)
    subscription = subscribe(session)
    coordination_lock_name = "launch_brief"
    started_at = perf_counter()

    async def researcher() -> dict[str, Any]:
        response, transcript = await client.complete_json(
            mode="with_memsmith",
            agent="researcher",
            system_prompt=_researcher_system_prompt(),
            user_prompt=_researcher_user_prompt(),
        )
        transcripts.append(transcript)
        await session.agent("researcher").push("facts", response)
        return response

    async def planner() -> dict[str, Any]:
        facts = await session.agent("planner").wait_for("researcher", "facts")
        async with session.agent("planner").lock(coordination_lock_name):
            response, transcript = await client.complete_json(
                mode="with_memsmith",
                agent="planner",
                system_prompt=_planner_system_prompt(),
                user_prompt=_planner_user_prompt(facts),
            )
        transcripts.append(transcript)
        await session.agent("planner").push("plan", response)
        return response

    async def reviewer() -> dict[str, Any]:
        facts = await session.agent("reviewer").wait_for("researcher", "facts")
        plan = await session.agent("reviewer").wait_for("planner", "plan")
        async with session.agent("reviewer").lock(coordination_lock_name):
            response, transcript = await client.complete_json(
                mode="with_memsmith",
                agent="reviewer",
                system_prompt=_reviewer_system_prompt(),
                user_prompt=_reviewer_user_prompt(facts, plan),
            )
        transcripts.append(transcript)
        await session.agent("reviewer").push("final_report", response)
        return response

    try:
        research_task = asyncio.create_task(researcher())
        planner_task = asyncio.create_task(planner())
        reviewer_task = asyncio.create_task(reviewer())

        research_output, plan_output, final_output = await asyncio.gather(
            research_task,
            planner_task,
            reviewer_task,
        )

        await session.broadcast(
            "workflow_complete",
            payload={"mode": "with_memsmith", "agents": ["researcher", "planner", "reviewer"]},
        )
        await session.checkpoint("final-proof")

        snapshot = await session.snapshot_state()
        history = await session.history()
        export_path = await session.export(mode_dir / "history_export.json")
        snapshot_payload = _serialize_snapshot(snapshot)
        _write_json(mode_dir / "state_snapshot.json", snapshot_payload)
        _write_json(mode_dir / "transcript.json", transcripts)
        artifacts.record("history_export", export_path)
        artifacts.record("state_snapshot", mode_dir / "state_snapshot.json")
        artifacts.record("transcript", mode_dir / "transcript.json")

        live_envelopes = await subscription.collect(timeout_ms=250)
        live_watch_text = render_watch(session_name, live_envelopes)
        live_watch_path = mode_dir / "runtime_watch.txt"
        live_watch_path.write_text(live_watch_text, encoding="utf-8")
        artifacts.record("runtime_watch", live_watch_path)

        history_operations = [event.operation for event in history]
    finally:
        subscription.close()
        session.close()

    dump_json_path = mode_dir / "dump_history.json"
    dump_exit_code, dump_output = await _capture_cli_output_async(
        ["dump", session_name, "--data-dir", str(data_dir), "--json-out", str(dump_json_path)]
    )
    dump_path = mode_dir / "dump.txt"
    dump_path.write_text(dump_output, encoding="utf-8")
    artifacts.record("dump_text", dump_path)
    artifacts.record("dump_json", dump_json_path)

    watch_exit_code, watch_output = await _capture_cli_output_async(
        ["watch", session_name, "--data-dir", str(data_dir), "--limit", "100", "--idle-timeout-ms", "250"]
    )
    watch_path = mode_dir / "persisted_watch.txt"
    watch_path.write_text(watch_output, encoding="utf-8")
    artifacts.record("persisted_watch", watch_path)

    resumed = await memsmith.resume(session_name, data_dir=data_dir)
    try:
        resumed_final = await resumed.agent("reviewer").get("final_report")
    finally:
        resumed.close()

    checkpoint_path = data_dir / session_name / "final-proof.checkpoint"
    checkpoint_sidecar_path = data_dir / session_name / "final-proof.checkpoint.json"
    wal_path = data_dir / session_name / "session.wal"
    artifacts.record("checkpoint", checkpoint_path)
    artifacts.record("checkpoint_sidecar", checkpoint_sidecar_path)
    artifacts.record("wal", wal_path)

    history_export_payload = _read_json_if_exists(export_path)
    dump_json_payload = _read_json_if_exists(dump_json_path)
    validation = _validate_workflow_outputs(research_output, plan_output, final_output)
    validation.update(
        {
            "dump_exit_code": dump_exit_code == 0,
            "watch_exit_code": watch_exit_code == 0,
            "history_export_exists": export_path.exists(),
            "history_export_has_entries": bool(history_export_payload),
            "snapshot_has_expected_keys": {
                "researcher:facts",
                "planner:plan",
                "reviewer:final_report",
            }
            <= set(snapshot_payload),
            "dump_contains_session_start": "SESSION START" in dump_output,
            "dump_contains_checkpoint": "CHECKPOINT" in dump_output,
            "dump_contains_broadcast": "BROADCAST" in dump_output,
            "dump_json_has_checkpoint": _history_has_operation(dump_json_payload, "CHECKPOINT"),
            "dump_json_has_push": _history_has_operation(dump_json_payload, "PUSH"),
            "watch_contains_wait": "WAIT_FOR_RESOLVE" in live_watch_text,
            "watch_contains_lock": "LOCK_" in live_watch_text,
            "watch_contains_push": "PUSH" in live_watch_text,
            "watch_contains_broadcast": "BROADCAST" in live_watch_text,
            "persisted_watch_contains_push": "PUSH" in watch_output,
            "persisted_watch_contains_broadcast": "BROADCAST" in watch_output,
            "resume_matches_final": resumed_final == final_output,
            "checkpoint_exists": checkpoint_path.exists(),
            "checkpoint_sidecar_exists": checkpoint_sidecar_path.exists(),
            "wal_exists": wal_path.exists(),
            "history_has_expected_operations": all(
                operation in history_operations
                for operation in [
                    "PUSH",
                    "WAIT_FOR_RESOLVE",
                    "LOCK_ACQUIRE",
                    "LOCK_RELEASE",
                    "BROADCAST",
                    "CHECKPOINT",
                ]
            ),
        }
    )

    duration_s = perf_counter() - started_at
    metrics = _summarize_transcripts(transcripts)
    quality = _assess_output_quality(research_output, plan_output, final_output)
    return ModeRunResult(
        mode="with_memsmith",
        success=all(bool(value) for value in validation.values()),
        duration_s=round(duration_s, 4),
        llm_calls=metrics["llm_calls"],
        prompt_tokens=metrics["prompt_tokens"],
        completion_tokens=metrics["completion_tokens"],
        total_tokens=metrics["total_tokens"],
        model=client.model,
        validation=validation,
        quality=quality,
        artifact_paths=artifacts.files,
        workflow_outputs={
            "research": research_output,
            "plan": plan_output,
            "final": final_output,
        },
        coordination_events=len(history_operations),
        notes=[
            "Used real wait, lock, checkpoint, resume, and broadcast flows.",
            "Captured runtime watch output plus persisted CLI watch and dump artifacts.",
        ],
    )


async def _run_without_memsmith(client: LiteLLMChatClient, mode_dir: Path) -> ModeRunResult:
    mode_dir.mkdir(parents=True, exist_ok=True)
    artifacts = ModeArtifacts(mode="without_memsmith", root=mode_dir)
    transcripts: list[dict[str, Any]] = []
    coordinator = ManualCoordinator()
    coordination_lock = asyncio.Lock()
    started_at = perf_counter()

    async def researcher() -> dict[str, Any]:
        response, transcript = await client.complete_json(
            mode="without_memsmith",
            agent="researcher",
            system_prompt=_researcher_system_prompt(),
            user_prompt=_researcher_user_prompt(),
        )
        transcripts.append(transcript)
        await coordinator.push("researcher", "facts", response)
        return response

    async def planner() -> dict[str, Any]:
        facts = await coordinator.wait_for("planner", "researcher", "facts")
        async with coordination_lock:
            coordinator.trace.append({"agent": "planner", "operation": "LOCK_ACQUIRE", "key": "launch_brief"})
            response, transcript = await client.complete_json(
                mode="without_memsmith",
                agent="planner",
                system_prompt=_planner_system_prompt(),
                user_prompt=_planner_user_prompt(facts),
            )
            coordinator.trace.append({"agent": "planner", "operation": "LOCK_RELEASE", "key": "launch_brief"})
        transcripts.append(transcript)
        await coordinator.push("planner", "plan", response)
        return response

    async def reviewer() -> dict[str, Any]:
        facts = await coordinator.wait_for("reviewer", "researcher", "facts")
        plan = await coordinator.wait_for("reviewer", "planner", "plan")
        async with coordination_lock:
            coordinator.trace.append({"agent": "reviewer", "operation": "LOCK_ACQUIRE", "key": "launch_brief"})
            response, transcript = await client.complete_json(
                mode="without_memsmith",
                agent="reviewer",
                system_prompt=_reviewer_system_prompt(),
                user_prompt=_reviewer_user_prompt(facts, plan),
            )
            coordinator.trace.append({"agent": "reviewer", "operation": "LOCK_RELEASE", "key": "launch_brief"})
        transcripts.append(transcript)
        await coordinator.push("reviewer", "final_report", response)
        coordinator.trace.append({"agent": "system", "operation": "WORKFLOW_COMPLETE", "key": "manual"})
        return response

    research_output, plan_output, final_output = await asyncio.gather(
        asyncio.create_task(researcher()),
        asyncio.create_task(planner()),
        asyncio.create_task(reviewer()),
    )
    duration_s = perf_counter() - started_at

    trace_path = mode_dir / "manual_trace.json"
    transcript_path = mode_dir / "transcript.json"
    shared_state_path = mode_dir / "shared_state.json"
    _write_json(trace_path, coordinator.trace)
    _write_json(transcript_path, transcripts)
    _write_json(shared_state_path, coordinator.values)
    artifacts.record("manual_trace", trace_path)
    artifacts.record("transcript", transcript_path)
    artifacts.record("shared_state", shared_state_path)

    validation = _validate_workflow_outputs(research_output, plan_output, final_output)
    validation.update(
        {
            "manual_trace_has_waits": any(item["operation"] == "WAIT_FOR_RESOLVE" for item in coordinator.trace),
            "manual_trace_has_locks": any(item["operation"].startswith("LOCK_") for item in coordinator.trace),
            "manual_trace_has_completion": any(item["operation"] == "WORKFLOW_COMPLETE" for item in coordinator.trace),
            "shared_state_has_expected_keys": {
                "researcher:facts",
                "planner:plan",
                "reviewer:final_report",
            }
            <= set(coordinator.values),
        }
    )
    metrics = _summarize_transcripts(transcripts)
    quality = _assess_output_quality(research_output, plan_output, final_output)
    return ModeRunResult(
        mode="without_memsmith",
        success=all(bool(value) for value in validation.values()),
        duration_s=round(duration_s, 4),
        llm_calls=metrics["llm_calls"],
        prompt_tokens=metrics["prompt_tokens"],
        completion_tokens=metrics["completion_tokens"],
        total_tokens=metrics["total_tokens"],
        model=client.model,
        validation=validation,
        quality=quality,
        artifact_paths=artifacts.files,
        workflow_outputs={
            "research": research_output,
            "plan": plan_output,
            "final": final_output,
        },
        coordination_events=len(coordinator.trace),
        notes=[
            "Manual baseline uses plain asyncio events and a raw trace log.",
            "No MemSmith dump, watch, checkpoint, or recovery artifacts exist in this mode.",
        ],
    )


def _researcher_system_prompt() -> str:
    return (
        "You are the Researcher in a three-agent coordination workflow. "
        "Return only valid JSON and copy fact values exactly from the source packet."
    )


def _researcher_user_prompt() -> str:
    return (
        f"{SCENARIO_BRIEF}\n\n"
        "Return JSON with this exact shape:\n"
        "{\n"
        '  "facts": {\n'
        '    "product_name": "",\n'
        '    "launch_date": "",\n'
        '    "budget_cap": "",\n'
        '    "team_shape": "",\n'
        '    "target_metric": "",\n'
        '    "success_metric": "",\n'
        '    "hard_requirement": "",\n'
        '    "primary_risk": ""\n'
        "  },\n"
        '  "must_have_actions": ["", "", ""],\n'
        '  "source_notes": ["", ""]\n'
        "}\n\n"
        "Requirements:\n"
        "- Keep the facts exact.\n"
        "- Keep must_have_actions as simple lowercase phrases.\n"
        "- Do not add new facts."
    )


def _planner_system_prompt() -> str:
    return (
        "You are the Planner in a three-agent coordination workflow. "
        "Use the research facts exactly as given and return only valid JSON."
    )


def _planner_user_prompt(facts: dict[str, Any]) -> str:
    return (
        f"Source packet:\n{SCENARIO_BRIEF}\n\n"
        f"Research facts JSON:\n{json.dumps(facts, indent=2)}\n\n"
        "Return JSON with this exact shape:\n"
        "{\n"
        '  "coordination_input_fact_ids": ["launch_date", "budget_cap", "team_shape", "target_metric", "success_metric", "hard_requirement", "primary_risk"],\n'
        '  "phases": [\n'
        '    {"name": "prep", "goal": "", "depends_on": ["", ""]},\n'
        '    {"name": "pilot", "goal": "", "depends_on": ["", ""]},\n'
        '    {"name": "launch", "goal": "", "depends_on": ["", ""]}\n'
        "  ],\n"
        '  "risk_register": [{"risk": "", "mitigation": ""}],\n'
        '  "handoff_to_reviewer": ""\n'
        "}\n\n"
        "Requirements:\n"
        "- Use exactly the phase names prep, pilot, launch.\n"
        "- Mention the hard requirement and the primary risk in the plan.\n"
        "- Keep coordination_input_fact_ids comprehensive."
    )


def _reviewer_system_prompt() -> str:
    return (
        "You are the Reviewer in a three-agent coordination workflow. "
        "Use the research facts and planner output exactly as inputs. Return only valid JSON."
    )


def _reviewer_user_prompt(facts: dict[str, Any], plan: dict[str, Any]) -> str:
    return (
        f"Source packet:\n{SCENARIO_BRIEF}\n\n"
        f"Research facts JSON:\n{json.dumps(facts, indent=2)}\n\n"
        f"Planner JSON:\n{json.dumps(plan, indent=2)}\n\n"
        "Return JSON with this exact shape:\n"
        "{\n"
        '  "product_name": "",\n'
        '  "launch_date": "",\n'
        '  "budget_cap": "",\n'
        '  "team_shape": "",\n'
        '  "target_metric": "",\n'
        '  "success_metric": "",\n'
        '  "hard_requirement": "",\n'
        '  "primary_risk": "",\n'
        '  "must_have_actions": ["", "", ""],\n'
        '  "phase_names": ["prep", "pilot", "launch"],\n'
        '  "used_fact_ids": ["", ""],\n'
        '  "quality_checks": ["", ""],\n'
        '  "final_summary": ""\n'
        "}\n\n"
        "Requirements:\n"
        "- Copy the canonical values exactly for the fact fields.\n"
        "- phase_names must be exactly prep, pilot, launch.\n"
        "- used_fact_ids must include every canonical fact except product_name.\n"
        "- quality_checks must mention onboarding docs and rollback drill."
    )


def _validate_workflow_outputs(
    research_output: dict[str, Any],
    plan_output: dict[str, Any],
    final_output: dict[str, Any],
) -> dict[str, bool]:
    research_facts = research_output.get("facts", {})
    research_ok = all(
        _normalize_text(research_facts.get(key)) == _normalize_text(value)
        for key, value in CANONICAL_FACTS.items()
    )
    actions_ok = sorted(_normalize_text(item) for item in research_output.get("must_have_actions", [])) == sorted(
        _normalize_text(item) for item in MUST_HAVE_ACTIONS
    )

    plan_phase_names = [phase.get("name") for phase in plan_output.get("phases", [])]
    plan_fact_ids = set(plan_output.get("coordination_input_fact_ids", []))
    plan_ok = (
        plan_phase_names == PHASE_NAMES
        and set(CANONICAL_FACTS) - {"product_name"} <= plan_fact_ids
        and _risk_register_covers_primary_risk(plan_output.get("risk_register", []))
    )

    final_fact_ok = all(
        _normalize_text(final_output.get(key)) == _normalize_text(value)
        for key, value in CANONICAL_FACTS.items()
    )
    final_actions_ok = sorted(_normalize_text(item) for item in final_output.get("must_have_actions", [])) == sorted(
        _normalize_text(item) for item in MUST_HAVE_ACTIONS
    )
    final_phase_ok = final_output.get("phase_names", []) == PHASE_NAMES
    used_fact_ids = set(final_output.get("used_fact_ids", []))
    final_used_inputs_ok = set(CANONICAL_FACTS) - {"product_name"} <= used_fact_ids
    final_quality_ok = _quality_checks_cover_requirements(final_output.get("quality_checks", []))

    return {
        "research_facts_exact": research_ok,
        "research_actions_exact": actions_ok,
        "planner_structure_valid": plan_ok,
        "final_facts_exact": final_fact_ok,
        "final_actions_exact": final_actions_ok,
        "final_phase_names_exact": final_phase_ok,
        "final_used_inputs_complete": final_used_inputs_ok,
        "final_quality_checks_present": final_quality_ok,
    }


def _assess_output_quality(
    research_output: dict[str, Any],
    plan_output: dict[str, Any],
    final_output: dict[str, Any],
) -> dict[str, Any]:
    required_fact_ids = set(CANONICAL_FACTS) - {"product_name"}

    research_facts = research_output.get("facts", {})
    exact_research_fact_count = sum(
        _normalize_text(research_facts.get(key)) == _normalize_text(value)
        for key, value in CANONICAL_FACTS.items()
    )
    matched_research_actions = _matched_items(research_output.get("must_have_actions", []), MUST_HAVE_ACTIONS)

    plan_phases = [phase.get("name") for phase in plan_output.get("phases", [])]
    matching_phase_count = sum(name == expected for name, expected in zip(plan_phases, PHASE_NAMES, strict=False))
    plan_fact_ids = set(plan_output.get("coordination_input_fact_ids", []))
    plan_risk_ok = _risk_register_covers_primary_risk(plan_output.get("risk_register", []))
    plan_handoff_ok = bool(_normalize_text(plan_output.get("handoff_to_reviewer")))

    exact_final_fact_count = sum(
        _normalize_text(final_output.get(key)) == _normalize_text(value)
        for key, value in CANONICAL_FACTS.items()
    )
    matched_final_actions = _matched_items(final_output.get("must_have_actions", []), MUST_HAVE_ACTIONS)
    final_phase_ok = final_output.get("phase_names", []) == PHASE_NAMES
    final_used_fact_ids = set(final_output.get("used_fact_ids", []))
    quality_check_hits = _quality_check_hit_count(final_output.get("quality_checks", []))

    breakdown = {
        "research_fact_grounding": exact_research_fact_count * 3,
        "research_action_grounding": len(matched_research_actions) * 2,
        "plan_phase_structure": matching_phase_count * 4,
        "plan_input_coverage": round(len(plan_fact_ids & required_fact_ids) / len(required_fact_ids) * 8),
        "plan_risk_grounding": 5 if plan_risk_ok else 0,
        "plan_handoff_quality": 5 if plan_handoff_ok else 0,
        "final_fact_grounding": exact_final_fact_count * 3,
        "final_action_grounding": len(matched_final_actions) * 2,
        "final_phase_structure": 4 if final_phase_ok else 0,
        "final_input_traceability": round(len(final_used_fact_ids & required_fact_ids) / len(required_fact_ids) * 3),
        "final_quality_checks": round(quality_check_hits / 2 * 3),
    }

    findings: list[str] = []
    if exact_research_fact_count != len(CANONICAL_FACTS):
        findings.append(
            f"Research facts exactness: {exact_research_fact_count}/{len(CANONICAL_FACTS)} canonical facts matched."
        )
    if len(matched_research_actions) != len(MUST_HAVE_ACTIONS):
        findings.append(
            f"Research actions exactness: {len(matched_research_actions)}/{len(MUST_HAVE_ACTIONS)} required actions matched."
        )
    if matching_phase_count != len(PHASE_NAMES):
        findings.append(f"Planner phases exactness: {matching_phase_count}/{len(PHASE_NAMES)} phase names matched.")
    if not required_fact_ids <= plan_fact_ids:
        findings.append(
            f"Planner input coverage: {len(plan_fact_ids & required_fact_ids)}/{len(required_fact_ids)} required fact ids included."
        )
    if plan_risk_ok is False:
        findings.append("Planner risk register did not ground the primary risk exactly.")
    if plan_handoff_ok is False:
        findings.append("Planner handoff_to_reviewer was empty.")
    if exact_final_fact_count != len(CANONICAL_FACTS):
        findings.append(
            f"Final brief exactness: {exact_final_fact_count}/{len(CANONICAL_FACTS)} canonical facts matched."
        )
    if len(matched_final_actions) != len(MUST_HAVE_ACTIONS):
        findings.append(
            f"Final brief actions: {len(matched_final_actions)}/{len(MUST_HAVE_ACTIONS)} required actions matched."
        )
    if final_phase_ok is False:
        findings.append("Final brief phase_names did not exactly match prep, pilot, launch.")
    if not required_fact_ids <= final_used_fact_ids:
        findings.append(
            f"Final brief traceability: {len(final_used_fact_ids & required_fact_ids)}/{len(required_fact_ids)} required fact ids cited."
        )
    if quality_check_hits < 2:
        findings.append("Final quality_checks did not mention both onboarding docs and rollback drill.")
    if not findings:
        findings.append("No deterministic quality gaps found for this run.")

    overall_score = sum(breakdown.values())
    return {
        "overall_score": overall_score,
        "max_score": 100,
        "breakdown": breakdown,
        "findings": findings,
    }


def _build_comparison_summary(with_memsmith: ModeRunResult, without_memsmith: ModeRunResult) -> dict[str, Any]:
    with_quality = int(with_memsmith.quality["overall_score"])
    without_quality = int(without_memsmith.quality["overall_score"])
    quality_delta = with_quality - without_quality
    quality_winner = _higher_value_winner(
        "with_memsmith",
        with_quality,
        "without_memsmith",
        without_quality,
    )

    return {
        "both_succeeded": with_memsmith.success and without_memsmith.success,
        "faster_mode": _lower_value_winner(
            with_memsmith.mode,
            with_memsmith.duration_s,
            without_memsmith.mode,
            without_memsmith.duration_s,
        ),
        "duration_delta_s": round(with_memsmith.duration_s - without_memsmith.duration_s, 4),
        "token_delta_total": with_memsmith.total_tokens - without_memsmith.total_tokens,
        "memsmith_artifact_count": len(with_memsmith.artifact_paths),
        "manual_artifact_count": len(without_memsmith.artifact_paths),
        "memsmith_has_explainability_artifacts": all(
            key in with_memsmith.artifact_paths
            for key in [
                "dump_text",
                "dump_json",
                "runtime_watch",
                "persisted_watch",
                "history_export",
                "checkpoint",
                "wal",
            ]
        ),
        "quality_score_with_memsmith": with_quality,
        "quality_score_without_memsmith": without_quality,
        "quality_score_delta": quality_delta,
        "quality_winner": quality_winner,
    }


def _build_suite_summary(comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    if not comparisons:
        return {
            "model_count": 0,
            "all_models_completed": False,
            "all_memsmith_runs_succeeded": False,
            "all_memsmith_runs_have_explainability": False,
            "manual_full_success_count": 0,
            "manual_full_failure_count": 0,
            "models_with_quality_gain": 0,
            "models_with_quality_tie": 0,
            "models_with_quality_drop": 0,
        }

    return {
        "model_count": len(comparisons),
        "all_models_completed": len(comparisons) > 0,
        "all_memsmith_runs_succeeded": all(item["with_memsmith"]["success"] for item in comparisons),
        "all_memsmith_runs_have_explainability": all(
            item["summary"]["memsmith_has_explainability_artifacts"] for item in comparisons
        ),
        "manual_full_success_count": sum(item["without_memsmith"]["success"] for item in comparisons),
        "manual_full_failure_count": sum(not item["without_memsmith"]["success"] for item in comparisons),
        "models_with_quality_gain": sum(
            item["summary"]["quality_winner"] == "with_memsmith" for item in comparisons
        ),
        "models_with_quality_tie": sum(item["summary"]["quality_winner"] == "tie" for item in comparisons),
        "models_with_quality_drop": sum(
            item["summary"]["quality_winner"] == "without_memsmith" for item in comparisons
        ),
        "average_duration_with_memsmith_s": round(
            sum(item["with_memsmith"]["duration_s"] for item in comparisons) / len(comparisons),
            4,
        ),
        "average_duration_without_memsmith_s": round(
            sum(item["without_memsmith"]["duration_s"] for item in comparisons) / len(comparisons),
            4,
        ),
        "average_quality_with_memsmith": round(
            sum(item["summary"]["quality_score_with_memsmith"] for item in comparisons) / len(comparisons),
            2,
        ),
        "average_quality_without_memsmith": round(
            sum(item["summary"]["quality_score_without_memsmith"] for item in comparisons) / len(comparisons),
            2,
        ),
    }


def _render_model_markdown_report(comparison: dict[str, Any]) -> str:
    summary = comparison["summary"]
    with_memsmith = comparison["with_memsmith"]
    without_memsmith = comparison["without_memsmith"]
    return "\n".join(
        [
            f"# Model benchmark: {comparison['model']}",
            "",
            f"Generated at: {comparison['generated_at']}",
            f"Artifacts root: {comparison['artifacts_root']}",
            "",
            "## Outcome",
            "",
            f"- Both modes succeeded: {summary['both_succeeded']}",
            f"- Faster mode: {summary['faster_mode']}",
            f"- Duration delta (with - without): {summary['duration_delta_s']}s",
            f"- Token delta (with - without): {summary['token_delta_total']}",
            f"- Quality score delta (with - without): {summary['quality_score_delta']}",
            f"- Quality winner: {summary['quality_winner']}",
            "",
            "## Benchmark table",
            "",
            "| Mode | Success | Duration (s) | Total tokens | Quality | Coordination events |",
            "|---|---|---:|---:|---:|---:|",
            f"| with_memsmith | {with_memsmith['success']} | {with_memsmith['duration_s']} | {with_memsmith['total_tokens']} | {with_memsmith['quality']['overall_score']} | {with_memsmith['coordination_events']} |",
            f"| without_memsmith | {without_memsmith['success']} | {without_memsmith['duration_s']} | {without_memsmith['total_tokens']} | {without_memsmith['quality']['overall_score']} | {without_memsmith['coordination_events']} |",
            "",
            "## MemSmith proof artifacts",
            "",
            *[f"- {key}: {value}" for key, value in with_memsmith["artifact_paths"].items()],
            "",
            "## Manual baseline artifacts",
            "",
            *[f"- {key}: {value}" for key, value in without_memsmith["artifact_paths"].items()],
        ]
    )


def _render_suite_markdown(suite_result: dict[str, Any]) -> str:
    lines = [
        "# MemSmith LiteLLM Benchmark Suite",
        "",
        f"Run id: {suite_result['run_id']}",
        f"Generated at: {suite_result['generated_at']}",
        f"Models requested: {', '.join(suite_result['models_requested'])}",
        "",
    ]

    summary = suite_result.get("summary", {})
    if summary:
        lines.extend(
            [
                "## Suite summary",
                "",
                f"- Models run: {summary['model_count']}",
                f"- All model comparisons completed: {summary['all_models_completed']}",
                f"- All MemSmith runs succeeded: {summary['all_memsmith_runs_succeeded']}",
                f"- All MemSmith runs kept explainability artifacts: {summary['all_memsmith_runs_have_explainability']}",
                f"- Manual baseline full-pass runs: {summary['manual_full_success_count']}",
                f"- Manual baseline degraded runs: {summary['manual_full_failure_count']}",
                f"- Models with quality gain from MemSmith: {summary['models_with_quality_gain']}",
                f"- Models with tied deterministic quality: {summary['models_with_quality_tie']}",
                f"- Models where baseline quality scored higher: {summary['models_with_quality_drop']}",
                "",
                "## Model matrix",
                "",
                "| Model | Success | Quality with | Quality without | Delta | Faster mode |",
                "|---|---|---:|---:|---:|---|",
            ]
        )
        for comparison in suite_result.get("comparisons", []):
            lines.append(
                f"| {comparison['model']} | {comparison['summary']['both_succeeded']} | "
                f"{comparison['summary']['quality_score_with_memsmith']} | "
                f"{comparison['summary']['quality_score_without_memsmith']} | "
                f"{comparison['summary']['quality_score_delta']} | {comparison['summary']['faster_mode']} |"
            )
        lines.append("")

    for comparison in suite_result.get("comparisons", []):
        lines.extend(
            [
                f"## {comparison['model']}",
                "",
                f"- Artifacts root: {comparison['artifacts_root']}",
                f"- Both modes succeeded: {comparison['summary']['both_succeeded']}",
                f"- Quality winner: {comparison['summary']['quality_winner']}",
                f"- Faster mode: {comparison['summary']['faster_mode']}",
                "",
            ]
        )

    return "\n".join(lines).rstrip()


def _render_console_report(suite_result: dict[str, Any]) -> str:
    lines = [
        "MemSmith LiteLLM Multi-Agent Evaluation",
        SECTION_RULE,
        f"Run id: {suite_result['run_id']}",
        f"Generated at: {suite_result['generated_at']}",
        f"Scenario: {suite_result['scenario']}",
        f"Models requested: {', '.join(suite_result['models_requested'])}",
        SECTION_RULE,
    ]

    summary = suite_result.get("summary", {})
    if summary:
        lines.extend(
            [
                "Suite summary",
                SUBSECTION_RULE,
                f"Models run: {summary['model_count']}",
                f"All model comparisons completed: {summary['all_models_completed']}",
                f"All MemSmith runs succeeded: {summary['all_memsmith_runs_succeeded']}",
                f"All MemSmith runs kept explainability artifacts: {summary['all_memsmith_runs_have_explainability']}",
                f"Manual baseline full-pass runs: {summary['manual_full_success_count']}",
                f"Manual baseline degraded runs: {summary['manual_full_failure_count']}",
                f"Average duration with MemSmith: {summary['average_duration_with_memsmith_s']}s",
                f"Average duration without MemSmith: {summary['average_duration_without_memsmith_s']}s",
                f"Average deterministic quality with MemSmith: {summary['average_quality_with_memsmith']}/100",
                f"Average deterministic quality without MemSmith: {summary['average_quality_without_memsmith']}/100",
                f"Quality gain runs: {summary['models_with_quality_gain']}",
                f"Quality tie runs: {summary['models_with_quality_tie']}",
                f"Quality drop runs: {summary['models_with_quality_drop']}",
                SECTION_RULE,
            ]
        )

    for comparison in suite_result.get("comparisons", []):
        with_memsmith = comparison["with_memsmith"]
        without_memsmith = comparison["without_memsmith"]
        summary = comparison["summary"]
        lines.extend(
            [
                f"Model: {comparison['model']}",
                SUBSECTION_RULE,
                f"Artifacts root: {comparison['artifacts_root']}",
                f"Both modes succeeded: {summary['both_succeeded']}",
                f"Faster mode: {summary['faster_mode']}",
                f"Duration delta (with - without): {summary['duration_delta_s']}s",
                f"Quality with MemSmith: {summary['quality_score_with_memsmith']}/100",
                f"Quality without MemSmith: {summary['quality_score_without_memsmith']}/100",
                f"Quality delta (with - without): {summary['quality_score_delta']}",
                f"Quality winner: {summary['quality_winner']}",
                "",
                "MemSmith quality findings",
                SUBSECTION_RULE,
                *[f"- {item}" for item in with_memsmith['quality']['findings']],
                "",
                "Manual baseline quality findings",
                SUBSECTION_RULE,
                *[f"- {item}" for item in without_memsmith['quality']['findings']],
                "",
                "MemSmith final output",
                SUBSECTION_RULE,
                _pretty_json(with_memsmith["workflow_outputs"]["final"]),
                "",
                "Manual baseline final output",
                SUBSECTION_RULE,
                _pretty_json(without_memsmith["workflow_outputs"]["final"]),
                "",
                "MemSmith runtime watch",
                SUBSECTION_RULE,
                _read_text_artifact(with_memsmith["artifact_paths"].get("runtime_watch")),
                "",
                "MemSmith persisted watch",
                SUBSECTION_RULE,
                _read_text_artifact(with_memsmith["artifact_paths"].get("persisted_watch")),
                "",
                "MemSmith dump",
                SUBSECTION_RULE,
                _read_text_artifact(with_memsmith["artifact_paths"].get("dump_text")),
                "",
                "Manual baseline trace",
                SUBSECTION_RULE,
                _read_json_artifact(without_memsmith["artifact_paths"].get("manual_trace")),
                SECTION_RULE,
            ]
        )

    return "\n".join(lines).rstrip()


def _render_failure_console_report(suite_result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "MemSmith LiteLLM Multi-Agent Evaluation",
            SECTION_RULE,
            f"Run id: {suite_result.get('run_id', 'unknown')}",
            f"Generated at: {suite_result.get('generated_at', 'unknown')}",
            f"Failure: {suite_result.get('error', 'unknown error')}",
            SECTION_RULE,
        ]
    )


def _summarize_transcripts(transcripts: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "llm_calls": len(transcripts),
        "prompt_tokens": sum(int(item.get("prompt_tokens", 0)) for item in transcripts),
        "completion_tokens": sum(int(item.get("completion_tokens", 0)) for item in transcripts),
        "total_tokens": sum(int(item.get("total_tokens", 0)) for item in transcripts),
    }


def _serialize_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {key: {"value": state.value, "version": state.version} for key, state in snapshot.items()}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _update_latest(run_dir: Path) -> None:
    latest_json = RESULTS_ROOT / "latest.json"
    latest_md = RESULTS_ROOT / "latest.md"
    latest_console = RESULTS_ROOT / "latest_console.txt"
    latest_pointer = RESULTS_ROOT / "latest_run.txt"

    source_json = _first_existing(run_dir / "suite.json", run_dir / "suite.failure.json")
    source_md = _first_existing(run_dir / "suite.md")
    source_console = _first_existing(run_dir / "console_report.txt", run_dir / "console_report.failure.txt")

    if source_json is not None:
        shutil.copyfile(source_json, latest_json)
    if source_md is not None:
        shutil.copyfile(source_md, latest_md)
    if source_console is not None:
        shutil.copyfile(source_console, latest_console)
    latest_pointer.write_text(str(run_dir), encoding="utf-8")


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().lower().split())


def _extract_json_object(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("Expected a JSON object response.")
        return parsed
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(text[start : end + 1])
        if not isinstance(parsed, dict):
            raise ValueError("Expected a JSON object response.")
        return parsed


def _capture_cli_output(argv: list[str]) -> tuple[int, str]:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = memsmith_cli_main(argv)
    return exit_code, buffer.getvalue()


async def _capture_cli_output_async(argv: list[str]) -> tuple[int, str]:
    return await asyncio.to_thread(_capture_cli_output, argv)


def _load_backend_env() -> dict[str, str]:
    env_path = BACKEND_ROOT / ".env"
    if not env_path.exists():
        return {}

    loaded: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = _strip_optional_quotes(value.strip())
        if key and key not in os.environ:
            os.environ[key] = value
        loaded[key] = value
    return loaded


def _strip_optional_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _parse_model_list(value: str) -> list[str]:
    if not value.strip():
        return []
    parts = re.split(r"[,\n]", value)
    return [item.strip() for item in parts if item.strip()]


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return slug.strip("-") or "model"


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _get_value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _extract_message_content(response: Any) -> str:
    choices = _get_value(response, "choices", [])
    if not choices:
        raise ValueError("LiteLLM response did not include any choices.")

    message = _get_value(choices[0], "message", choices[0])
    content = _get_value(message, "content", "")
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text_value = item.get("text") or item.get("content") or item.get("value")
                if text_value is not None:
                    parts.append(str(text_value))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part).strip()
    return str(content).strip()


def _extract_usage(response: Any) -> dict[str, int]:
    usage = _get_value(response, "usage", {}) or {}
    return {
        "prompt_tokens": int(_get_value(usage, "prompt_tokens", 0) or 0),
        "completion_tokens": int(_get_value(usage, "completion_tokens", 0) or 0),
        "total_tokens": int(_get_value(usage, "total_tokens", 0) or 0),
    }


def _matched_items(items: list[Any], expected: list[str]) -> list[str]:
    normalized_expected = {_normalize_text(item) for item in expected}
    matched = []
    for item in items:
        normalized = _normalize_text(item)
        if normalized in normalized_expected:
            matched.append(normalized)
    return sorted(set(matched))


def _lower_value_winner(first_label: str, first_value: float, second_label: str, second_value: float) -> str:
    if first_value < second_value:
        return first_label
    if second_value < first_value:
        return second_label
    return "tie"


def _higher_value_winner(first_label: str, first_value: float, second_label: str, second_value: float) -> str:
    if first_value > second_value:
        return first_label
    if second_value > first_value:
        return second_label
    return "tie"


def _risk_register_covers_primary_risk(risk_register: list[Any]) -> bool:
    target = _normalize_text(CANONICAL_FACTS["primary_risk"])
    for item in risk_register:
        risk_text = _normalize_text(item.get("risk")) if isinstance(item, dict) else _normalize_text(item)
        if target and target in risk_text:
            return True
    return False


def _quality_check_hit_count(quality_checks: list[Any]) -> int:
    text = " ".join(_normalize_text(item) for item in quality_checks)
    onboarding_ok = "onboarding" in text and ("doc" in text or "document" in text)
    rollback_ok = "rollback" in text and ("drill" in text or "procedure" in text or "recover" in text)
    return int(onboarding_ok) + int(rollback_ok)


def _quality_checks_cover_requirements(quality_checks: list[Any]) -> bool:
    return _quality_check_hit_count(quality_checks) == 2


def _pretty_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def _read_text_artifact(path_str: str | None) -> str:
    if not path_str:
        return "Artifact not found."
    path = Path(path_str)
    if not path.exists():
        return f"Artifact missing: {path}"
    return path.read_text(encoding="utf-8")


def _read_json_artifact(path_str: str | None) -> str:
    if not path_str:
        return "Artifact not found."
    path = Path(path_str)
    if not path.exists():
        return f"Artifact missing: {path}"
    return _pretty_json(json.loads(path.read_text(encoding="utf-8")))


def _read_json_if_exists(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _history_has_operation(history_payload: Any, operation: str) -> bool:
    if not isinstance(history_payload, list):
        return False
    return any(item.get("operation") == operation for item in history_payload if isinstance(item, dict))


def _first_existing(*paths: Path) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None