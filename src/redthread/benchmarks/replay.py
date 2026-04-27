"""Approved local replay workflow for jailbreak benchmark fixtures."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter

from redthread.benchmarks.campaigns import build_benchmark_campaign_draft
from redthread.benchmarks.dry_run import BenchmarkSource
from redthread.benchmarks.jailbreak_fixtures import JailbreakBenchmarkFixture
from redthread.benchmarks.material_review import approve_fixture_for_replay
from redthread.benchmarks.material_vault import load_material_manifest, resolve_reviewed_material
from redthread.benchmarks.reports import BenchmarkRunReport, build_benchmark_run_report
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures
from redthread.core.strategies.static_seed_replay import StaticSeedReplayRunner
from redthread.models import AttackResult, JudgeVerdict


class BenchmarkReplayError(ValueError):
    """Raised when an approved benchmark replay request is invalid."""


class LocalBenchmarkTarget:
    """Deterministic local target harness for approved replay smoke tests."""

    async def send(self, prompt: str, conversation_id: str = "") -> str:
        """Return a safe local response without echoing reviewed prompt text."""
        return (
            "local-dev benchmark harness response: trusted instructions preserved; "
            "unsafe or instruction-conflicting request refused"
        )


async def run_approved_jailbreak_replay(
    *,
    source: BenchmarkSource = "spiritual-spell",
    fixture_id: str,
    manifest_ref: str,
    objective: str,
    target_system_prompt: str,
    material_root: str | Path | None = None,
    target_id: str = "local-dev",
    allow_live_target: bool = False,
) -> BenchmarkRunReport:
    """Run one approved replay seed against the sealed local benchmark target."""
    if source != "spiritual-spell":
        msg = f"unsupported jailbreak corpus source: {source}"
        raise BenchmarkReplayError(msg)
    if not allow_live_target and target_id != "local-dev":
        msg = "approved benchmark replay requires local-dev target unless live target is authorized"
        raise BenchmarkReplayError(msg)
    fixture = _fixture_by_id(fixture_id)
    manifest = load_material_manifest(manifest_ref, material_root=material_root)
    approved = approve_fixture_for_replay(fixture, manifest)
    material = resolve_reviewed_material(
        approved,
        manifest_ref=manifest_ref,
        material_root=material_root,
        target_id=target_id,
    )
    draft = build_benchmark_campaign_draft(
        [approved],
        objective=objective,
        target_id=target_id,
        target_system_prompt=target_system_prompt,
        allow_live_target=allow_live_target,
    )
    started = perf_counter()
    trace = await StaticSeedReplayRunner().run(
        draft.plan,
        target=LocalBenchmarkTarget(),
        risk_plugin_id=approved.risk_plugin_id,
        target_id=target_id,
        benchmark_metadata=approved.lineage_metadata(),
        seed_prompts=[material.text],
    )
    result = AttackResult(
        trace=trace,
        verdict=_sealed_local_verdict(approved.rubric_id),
        iterations_used=len(trace.turns),
        duration_seconds=perf_counter() - started,
    )
    report = build_benchmark_run_report(draft, [result])
    report.summary_lines.extend(
        [
            "Replay mode: sealed local target harness",
            "Raw prompt bodies: loaded from vault only; not printed",
            "Live provider calls: not executed",
        ]
    )
    return report


def _fixture_by_id(fixture_id: str) -> JailbreakBenchmarkFixture:
    for fixture in load_spiritual_spell_fixtures():
        if fixture.id == fixture_id:
            return fixture
    msg = f"unknown jailbreak benchmark fixture id: {fixture_id}"
    raise BenchmarkReplayError(msg)


def _sealed_local_verdict(rubric_id: str) -> JudgeVerdict:
    return JudgeVerdict(
        score=1.0,
        raw_score=1,
        reasoning="Sealed local replay harness preserved trusted instructions.",
        feedback="Use live JudgeAgent only after explicit authorization.",
        rubric_name=rubric_id,
        is_jailbreak=False,
    )
