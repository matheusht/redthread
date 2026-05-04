"""Operator reports for jailbreak benchmark runs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, Field

from redthread.benchmarks.campaigns import BenchmarkCampaignDraft
from redthread.benchmarks.models import (
    BenchmarkEvidenceMode,
    BenchmarkNotScoredReason,
    BenchmarkPromotionImpact,
    BenchmarkRunMode,
    BenchmarkScorecard,
)
from redthread.core.regression_cases import finding_regression_link
from redthread.models import AttackResult
from redthread.orchestration.models import RegressionCase


class BenchmarkVerdictSummary(BaseModel):
    """Small report row for one benchmark result."""

    result_id: str
    trace_id: str
    fixture_id: str
    risk_plugin_id: str
    strategy_id: str
    judge_score: float
    is_jailbreak: bool
    detector_hint_note: str = "detector hints are weak signals, not verdicts"


class BenchmarkRunReport(BaseModel):
    """Operator-readable report payload for benchmark runs."""

    schema_version: str = "redthread.jailbreak_benchmark_report.v1"
    evidence_mode: BenchmarkEvidenceMode = BenchmarkEvidenceMode.JUDGE_CONFIRMED_SANDBOX
    run_mode: BenchmarkRunMode = BenchmarkRunMode.SANDBOX_REPLAY
    promotion_impact: BenchmarkPromotionImpact = BenchmarkPromotionImpact.FINDING_CANDIDATE
    not_scored_reason: BenchmarkNotScoredReason | None = None
    scorecard: BenchmarkScorecard | None = None
    tested_fixture_ids: list[str] = Field(default_factory=list)
    blocked_fixture_ids: list[str] = Field(default_factory=list)
    verdicts: list[BenchmarkVerdictSummary] = Field(default_factory=list)
    regression_links: list[dict[str, Any]] = Field(default_factory=list)
    summary_lines: list[str] = Field(default_factory=list)
    detector_hint_note: str = "Detector hints are weak signals. JudgeAgent owns verdicts."


def build_benchmark_run_report(
    draft: BenchmarkCampaignDraft,
    results: Sequence[AttackResult],
    *,
    regression_cases: Mapping[str, RegressionCase] | None = None,
    evidence_mode: BenchmarkEvidenceMode = BenchmarkEvidenceMode.JUDGE_CONFIRMED_SANDBOX,
    run_mode: BenchmarkRunMode = BenchmarkRunMode.SANDBOX_REPLAY,
    promotion_impact: BenchmarkPromotionImpact = BenchmarkPromotionImpact.FINDING_CANDIDATE,
    not_scored_reason: BenchmarkNotScoredReason | None = None,
    scorecard: BenchmarkScorecard | None = None,
) -> BenchmarkRunReport:
    """Build a report for benchmark run results and optional regression links."""
    regression_cases = regression_cases or {}
    verdicts = [_verdict_summary(result) for result in results]
    regression_links = [
        finding_regression_link(result, regression_cases[result.id])
        for result in results
        if result.id in regression_cases
    ]
    score_line = (
        f"Scorecard: not scored ({not_scored_reason.value})"
        if not_scored_reason
        else "Scorecard: eligible after deterministic aggregation"
    )
    summary_lines = [
        *draft.summary_lines(),
        f"Evidence mode: {evidence_mode.value}",
        f"Promotion impact: {promotion_impact.value}",
        f"Results scored: {len(results)}",
        f"JudgeAgent jailbreaks: {sum(1 for result in results if result.verdict.is_jailbreak)}",
        f"Regression links: {len(regression_links)}",
        score_line,
        "Detector hints are weak signals. JudgeAgent owns verdicts.",
    ]
    return BenchmarkRunReport(
        evidence_mode=evidence_mode,
        run_mode=run_mode,
        promotion_impact=promotion_impact,
        not_scored_reason=not_scored_reason,
        scorecard=scorecard,
        tested_fixture_ids=[fixture.id for fixture in draft.fixtures],
        blocked_fixture_ids=draft.blocked_fixture_ids,
        verdicts=verdicts,
        regression_links=regression_links,
        summary_lines=summary_lines,
    )


def _verdict_summary(result: AttackResult) -> BenchmarkVerdictSummary:
    metadata = result.trace.metadata
    return BenchmarkVerdictSummary(
        result_id=result.id,
        trace_id=result.trace.id,
        fixture_id=str(metadata.get("benchmark_fixture_id", "")),
        risk_plugin_id=str(metadata.get("risk_plugin_id", "unknown")),
        strategy_id=str(metadata.get("strategy_id", result.trace.algorithm)),
        judge_score=result.verdict.score,
        is_jailbreak=result.verdict.is_jailbreak,
    )
