"""Live Groq-backed benchmark for a manual three-agent workflow."""

from __future__ import annotations

import asyncio
import io
import json
import os
import shutil
from contextlib import redirect_stdout
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib import error, request

import memsmith
from memsmith.cli.main import main as memsmith_cli_main
from memsmith.observability.watch import render_watch, subscribe

BACKEND_ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = Path(__file__).resolve().parent / "results"
RUN_OPT_IN_ENV = "RUN_GROQ_MULTIAGENT_SMOKE"
GROQ_API_KEY_ENV = "GROQ_API_KEY"
GROQ_MODEL_ENV = "GROQ_MODEL"

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
PREFERRED_MODELS = (
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
)


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
    artifact_paths: dict[str, str]
    final_payload: dict[str, Any]
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


class GroqChatClient:
    """Minimal OpenAI-compatible Groq client using the standard library."""

    def __init__(self, api_key: str, *, timeout_s: float = 90.0) -> None:
        self._api_key = api_key
        self._timeout_s = timeout_s
        self._base_url = "https://api.groq.com/openai/v1"
        self._resolved_model: str | None = None

    @property
    def model(self) -> str:
        if self._resolved_model is None:
            self._resolved_model = self._resolve_model()
        return self._resolved_model

    async def complete_json(
        self,
        *,
        mode: str,
        agent: str,
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        return await asyncio.to_thread(
            self._complete_json_sync,
            mode,
            agent,
            system_prompt,
            user_prompt,
        )

    def _complete_json_sync(
        self,
        mode: str,
        agent: str,
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        last_error: Exception | None = None
        for attempt in range(1, 4):
            started_at = perf_counter()
            try:
                response = self._request_json(
                    "POST",
                    "/chat/completions",
                    payload={
                        "model": self.model,
                        "temperature": 0.2,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                    },
                )
                content = response["choices"][0]["message"]["content"]
                parsed = _extract_json_object(content)
            except Exception as exc:  # pragma: no cover - exercised by live opt-in runs only
                last_error = exc
                if attempt == 3:
                    raise RuntimeError(f"Groq completion failed for {mode}/{agent}: {exc}") from exc
                continue

            latency_s = perf_counter() - started_at
            usage = response.get("usage", {})
            transcript = {
                "mode": mode,
                "agent": agent,
                "attempt": attempt,
                "model": response.get("model", self.model),
                "latency_s": round(latency_s, 4),
                "prompt_tokens": int(usage.get("prompt_tokens", 0)),
                "completion_tokens": int(usage.get("completion_tokens", 0)),
                "total_tokens": int(usage.get("total_tokens", 0)),
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response": parsed,
            }
            return parsed, transcript

        raise RuntimeError(f"Groq completion failed for {mode}/{agent}: {last_error}")

    def _resolve_model(self) -> str:
        configured_model = os.getenv(GROQ_MODEL_ENV)
        if configured_model:
            return configured_model

        try:
            response = self._request_json("GET", "/models")
            available = [item["id"] for item in response.get("data", []) if "id" in item]
        except Exception:  # pragma: no cover - exercised by live opt-in runs only
            available = list(PREFERRED_MODELS)

        for preferred in PREFERRED_MODELS:
            if preferred in available:
                return preferred
        if available:
            return available[0]
        raise RuntimeError("Could not resolve a Groq model for the live benchmark.")

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
            "User-Agent": "memsmith-live-benchmark/0.1",
        }
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(payload).encode("utf-8")

        req = request.Request(url, data=body, headers=headers, method=method)

        try:
            with request.urlopen(req, timeout=self._timeout_s) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:  # pragma: no cover - exercised by live opt-in runs only
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Groq HTTP {exc.code}: {detail}") from exc


def should_run_live_smoke() -> bool:
    return _truthy(os.getenv(RUN_OPT_IN_ENV, ""))


def has_groq_api_key() -> bool:
    return bool(resolve_groq_api_key())


def resolve_groq_api_key() -> str | None:
    configured = os.getenv(GROQ_API_KEY_ENV)
    if configured:
        return configured

    env_path = BACKEND_ROOT / ".env"
    if not env_path.exists():
        return None

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() == GROQ_API_KEY_ENV:
            return value.strip()
    return None


def run_live_benchmark() -> dict[str, Any]:
    api_key = resolve_groq_api_key()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY was not found in the environment or backend/.env.")
    return asyncio.run(_run_live_benchmark(api_key))


async def _run_live_benchmark(api_key: str) -> dict[str, Any]:
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    run_dir = RESULTS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    comparison: dict[str, Any] = {
        "run_id": run_id,
        "scenario": SCENARIO_NAME,
        "generated_at": datetime.now().astimezone().isoformat(),
    }

    client = GroqChatClient(api_key)
    try:
        with_memsmith = await _run_with_memsmith(client, run_dir / "with_memsmith")
        without_memsmith = await _run_without_memsmith(client, run_dir / "without_memsmith")
        comparison["with_memsmith"] = asdict(with_memsmith)
        comparison["without_memsmith"] = asdict(without_memsmith)
        comparison["summary"] = _build_comparison_summary(with_memsmith, without_memsmith)
        _write_json(run_dir / "comparison.json", comparison)
        (run_dir / "comparison.md").write_text(_render_markdown_report(comparison), encoding="utf-8")
        _update_latest(run_dir)
        return comparison
    except Exception as exc:
        comparison["error"] = str(exc)
        _write_json(run_dir / "comparison.failure.json", comparison)
        _update_latest(run_dir)
        raise


async def _run_with_memsmith(client: GroqChatClient, mode_dir: Path) -> ModeRunResult:
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
        artifacts.record("history_export", export_path)
        _write_json(mode_dir / "state_snapshot.json", _serialize_snapshot(snapshot))
        artifacts.record("state_snapshot", mode_dir / "state_snapshot.json")
        _write_json(mode_dir / "transcript.json", transcripts)
        artifacts.record("transcript", mode_dir / "transcript.json")

        live_envelopes = await subscription.collect(timeout_ms=200)
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

    validation = _validate_workflow_outputs(research_output, plan_output, final_output)
    validation.update(
        {
            "dump_exit_code": dump_exit_code == 0,
            "watch_exit_code": watch_exit_code == 0,
            "dump_contains_checkpoint": "CHECKPOINT" in dump_output,
            "dump_contains_broadcast": "BROADCAST" in dump_output,
            "watch_contains_wait": "WAIT_FOR_RESOLVE" in live_watch_text,
            "watch_contains_lock": "LOCK_" in live_watch_text,
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
        artifact_paths=artifacts.files,
        final_payload=final_output,
        coordination_events=len(history_operations),
        notes=[
            "Used real wait/lock/checkpoint/broadcast flows.",
            "Captured runtime watch output plus persisted CLI watch and dump artifacts.",
        ],
    )


async def _run_without_memsmith(client: GroqChatClient, mode_dir: Path) -> ModeRunResult:
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
        }
    )
    metrics = _summarize_transcripts(transcripts)
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
        artifact_paths=artifacts.files,
        final_payload=final_output,
        coordination_events=len(coordinator.trace),
        notes=[
            "Manual baseline uses plain asyncio events and a raw trace log.",
            "No MemSmith dump/watch/checkpoint/recovery artifacts exist in this mode.",
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
    research_ok = all(_normalize_text(research_facts.get(key)) == _normalize_text(value) for key, value in CANONICAL_FACTS.items())
    actions_ok = sorted(_normalize_text(item) for item in research_output.get("must_have_actions", [])) == sorted(
        _normalize_text(item) for item in MUST_HAVE_ACTIONS
    )

    plan_phase_names = [phase.get("name") for phase in plan_output.get("phases", [])]
    plan_fact_ids = set(plan_output.get("coordination_input_fact_ids", []))
    plan_ok = (
        plan_phase_names == PHASE_NAMES
        and set(CANONICAL_FACTS) - {"product_name"} <= plan_fact_ids
        and any(
            _normalize_text(item.get("risk")) == _normalize_text(CANONICAL_FACTS["primary_risk"])
            for item in plan_output.get("risk_register", [])
        )
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
    quality_checks = " ".join(final_output.get("quality_checks", []))
    final_quality_ok = "onboarding docs" in quality_checks.lower() and "rollback drill" in quality_checks.lower()

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


def _build_comparison_summary(with_memsmith: ModeRunResult, without_memsmith: ModeRunResult) -> dict[str, Any]:
    faster_mode = with_memsmith.mode if with_memsmith.duration_s < without_memsmith.duration_s else without_memsmith.mode
    return {
        "both_succeeded": with_memsmith.success and without_memsmith.success,
        "faster_mode": faster_mode,
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
    }


def _render_markdown_report(comparison: dict[str, Any]) -> str:
    with_memsmith = comparison["with_memsmith"]
    without_memsmith = comparison["without_memsmith"]
    summary = comparison["summary"]
    return "\n".join(
        [
            f"# Multi-agent benchmark: {comparison['scenario']}",
            "",
            f"Run id: {comparison['run_id']}",
            f"Generated at: {comparison['generated_at']}",
            "",
            "## Outcome",
            "",
            f"- Both modes succeeded: {summary['both_succeeded']}",
            f"- Faster mode: {summary['faster_mode']}",
            f"- Duration delta (with - without): {summary['duration_delta_s']}s",
            f"- Token delta (with - without): {summary['token_delta_total']}",
            "",
            "## Benchmark table",
            "",
            "| Mode | Success | Duration (s) | LLM calls | Total tokens | Coordination events |",
            "|---|---|---:|---:|---:|---:|",
            f"| with_memsmith | {with_memsmith['success']} | {with_memsmith['duration_s']} | {with_memsmith['llm_calls']} | {with_memsmith['total_tokens']} | {with_memsmith['coordination_events']} |",
            f"| without_memsmith | {without_memsmith['success']} | {without_memsmith['duration_s']} | {without_memsmith['llm_calls']} | {without_memsmith['total_tokens']} | {without_memsmith['coordination_events']} |",
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


def _summarize_transcripts(transcripts: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "llm_calls": len(transcripts),
        "prompt_tokens": sum(int(item.get("prompt_tokens", 0)) for item in transcripts),
        "completion_tokens": sum(int(item.get("completion_tokens", 0)) for item in transcripts),
        "total_tokens": sum(int(item.get("total_tokens", 0)) for item in transcripts),
    }


def _serialize_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        key: {"value": state.value, "version": state.version}
        for key, state in snapshot.items()
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _update_latest(run_dir: Path) -> None:
    latest_json = RESULTS_ROOT / "latest.json"
    latest_md = RESULTS_ROOT / "latest.md"
    latest_pointer = RESULTS_ROOT / "latest_run.txt"

    comparison_json = run_dir / "comparison.json"
    failure_json = run_dir / "comparison.failure.json"
    source_json = comparison_json if comparison_json.exists() else failure_json
    if source_json.exists():
        shutil.copyfile(source_json, latest_json)
    comparison_md = run_dir / "comparison.md"
    if comparison_md.exists():
        shutil.copyfile(comparison_md, latest_md)
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