"""Approved local replay workflow for jailbreak benchmark fixtures."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter

from pydantic import BaseModel

from redthread.benchmarks.campaigns import build_benchmark_campaign_draft
from redthread.benchmarks.dry_run import BenchmarkSource
from redthread.benchmarks.jailbreak_fixtures import JailbreakBenchmarkFixture
from redthread.benchmarks.live_replay_gate import LIVE_REPLAY_DEFERRED_MESSAGE
from redthread.benchmarks.material_review import approve_fixture_for_replay
from redthread.benchmarks.material_vault import load_material_manifest, resolve_reviewed_material
from redthread.benchmarks.models import (
    BenchmarkEvidenceMode,
    BenchmarkLane,
    BenchmarkNotScoredReason,
    BenchmarkPromotionImpact,
    BenchmarkRunMode,
)
from redthread.benchmarks.regression_handoff import (
    BenchmarkRegressionHandoffArtifact,
    build_benchmark_regression_handoff,
)
from redthread.benchmarks.reports import BenchmarkRunReport, build_benchmark_run_report
from redthread.benchmarks.scoring import build_unscored_scorecard
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures
from redthread.core.strategies.static_seed_replay import StaticSeedReplayRunner
from redthread.models import AttackResult, JudgeVerdict


class BenchmarkReplayError(ValueError):
    """Raised when an approved benchmark replay request is invalid."""


class ApprovedBenchmarkReplayBundle(BaseModel):
    """Replay report plus optional prompt-safe regression handoff."""

    report: BenchmarkRunReport
    regression_handoff: BenchmarkRegressionHandoffArtifact | None = None


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
    bundle = await run_approved_jailbreak_replay_with_regression_handoff(
        source=source,
        fixture_id=fixture_id,
        manifest_ref=manifest_ref,
        objective=objective,
        target_system_prompt=target_system_prompt,
        material_root=material_root,
        target_id=target_id,
        allow_live_target=allow_live_target,
        include_regression_handoff=False,
    )
    return bundle.report


async def run_approved_jailbreak_replay_with_regression_handoff(
    *,
    source: BenchmarkSource = "spiritual-spell",
    fixture_id: str,
    manifest_ref: str,
    objective: str,
    target_system_prompt: str,
    material_root: str | Path | None = None,
    target_id: str = "local-dev",
    allow_live_target: bool = False,
    include_regression_handoff: bool = True,
) -> ApprovedBenchmarkReplayBundle:
    """Run approved replay and optionally build a prompt-safe regression handoff."""
    if source != "spiritual-spell":
        msg = f"unsupported jailbreak corpus source: {source}"
        raise BenchmarkReplayError(msg)
    if target_id != "local-dev":
        raise BenchmarkReplayError(LIVE_REPLAY_DEFERRED_MESSAGE)
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
    scorecard = build_unscored_scorecard(
        lane=BenchmarkLane.JAILBREAK,
        source=source,
        target_id=target_id,
        evidence_mode=BenchmarkEvidenceMode.SEALED_LOCAL_REPLAY,
        run_mode=BenchmarkRunMode.SEALED_REPLAY,
        promotion_impact=BenchmarkPromotionImpact.HARNESS_SMOKE_ONLY,
        not_scored_reason=BenchmarkNotScoredReason.SEALED_LOCAL_SMOKE_ONLY,
        fixture_ids=[approved.id],
        denominator=1,
        limitations=["Sealed local replay checks harness wiring only, not live target safety."],
    )
    report = build_benchmark_run_report(
        draft,
        [result],
        evidence_mode=BenchmarkEvidenceMode.SEALED_LOCAL_REPLAY,
        run_mode=BenchmarkRunMode.SEALED_REPLAY,
        promotion_impact=BenchmarkPromotionImpact.HARNESS_SMOKE_ONLY,
        not_scored_reason=BenchmarkNotScoredReason.SEALED_LOCAL_SMOKE_ONLY,
        scorecard=scorecard,
    )
    report.summary_lines.extend(
        [
            "Replay mode: sealed local target harness",
            "Raw prompt bodies: loaded from vault only; not printed",
            "Live provider calls: not executed",
            "This replay checks harness wiring only. It is not live target safety proof.",
        ]
    )
    handoff = None
    if include_regression_handoff:
        handoff = build_benchmark_regression_handoff(
            draft,
            [result],
            manifest=manifest,
            manifest_ref=manifest_ref,
        )
    return ApprovedBenchmarkReplayBundle(report=report, regression_handoff=handoff)


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
