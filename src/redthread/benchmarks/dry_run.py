"""Dry-run reports for benchmark corpus CLI surfaces."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, Field

from redthread.benchmarks.hints import BenchmarkHintProfile, build_fixture_hint_profiles
from redthread.benchmarks.jailbreak_fixtures import JailbreakBenchmarkFixture
from redthread.benchmarks.models import (
    BenchmarkEvidenceMode,
    BenchmarkLane,
    BenchmarkNotScoredReason,
    BenchmarkPromotionImpact,
    BenchmarkRunMode,
    BenchmarkScorecard,
)
from redthread.benchmarks.scoring import build_unscored_scorecard
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures

BenchmarkSource = Literal["spiritual-spell"]


class BenchmarkDryRunError(ValueError):
    """Raised when a benchmark dry-run request is invalid."""


class BenchmarkDryRunReport(BaseModel):
    """Metadata-only benchmark dry-run report."""

    schema_version: str = "redthread.jailbreak_benchmark_dry_run.v1"
    source: BenchmarkSource
    target_id: str
    evidence_mode: BenchmarkEvidenceMode = BenchmarkEvidenceMode.METADATA_ONLY
    run_mode: BenchmarkRunMode = BenchmarkRunMode.DRY_RUN
    promotion_impact: BenchmarkPromotionImpact = BenchmarkPromotionImpact.NONE
    not_scored_reason: BenchmarkNotScoredReason = BenchmarkNotScoredReason.DRY_RUN_NO_EXECUTION
    total_fixture_count: int
    selected_fixture_ids: list[str] = Field(default_factory=list)
    executable_fixture_ids: list[str] = Field(default_factory=list)
    blocked_fixture_ids: list[str] = Field(default_factory=list)
    hint_profiles: list[BenchmarkHintProfile] = Field(default_factory=list)
    scorecard: BenchmarkScorecard | None = None
    summary_lines: list[str] = Field(default_factory=list)
    raw_prompt_policy: str = "raw prompt bodies are not loaded during dry-run"


def build_jailbreak_corpus_dry_run_report(
    *,
    source: BenchmarkSource = "spiritual-spell",
    fixture_ids: Sequence[str] = (),
    families: Sequence[str] = (),
    target_id: str = "local-dev",
    allow_live_target: bool = False,
    limit: int = 25,
    include_hints: bool = False,
) -> BenchmarkDryRunReport:
    """Build a metadata-only dry-run report for a jailbreak benchmark source."""
    if source != "spiritual-spell":
        msg = f"unsupported jailbreak corpus source: {source}"
        raise BenchmarkDryRunError(msg)
    if not allow_live_target and target_id != "local-dev":
        msg = "benchmark dry-run requires local-dev target unless live target is authorized"
        raise BenchmarkDryRunError(msg)
    if limit < 1:
        msg = "benchmark dry-run limit must be at least 1"
        raise BenchmarkDryRunError(msg)
    fixtures = load_spiritual_spell_fixtures()
    selected = _filter_fixtures(fixtures, fixture_ids=fixture_ids, families=families)[:limit]
    if not selected:
        msg = "no benchmark fixtures matched the dry-run filters"
        raise BenchmarkDryRunError(msg)
    hints = build_fixture_hint_profiles(selected) if include_hints else []
    executable_ids = [fixture.id for fixture in selected if fixture.is_executable]
    blocked_ids = [fixture.id for fixture in selected if not fixture.is_executable]
    scorecard = build_unscored_scorecard(
        lane=BenchmarkLane.JAILBREAK,
        source=source,
        target_id=target_id,
        evidence_mode=BenchmarkEvidenceMode.METADATA_ONLY,
        run_mode=BenchmarkRunMode.DRY_RUN,
        promotion_impact=BenchmarkPromotionImpact.NONE,
        not_scored_reason=BenchmarkNotScoredReason.DRY_RUN_NO_EXECUTION,
        fixture_ids=[fixture.id for fixture in selected],
        denominator=len(selected),
        blocked_count=len(blocked_ids),
        limitations=["Dry-run uses fixture metadata only and does not execute target calls."],
    )
    return BenchmarkDryRunReport(
        source=source,
        target_id=target_id,
        total_fixture_count=len(fixtures),
        selected_fixture_ids=[fixture.id for fixture in selected],
        executable_fixture_ids=executable_ids,
        blocked_fixture_ids=blocked_ids,
        hint_profiles=hints,
        scorecard=scorecard,
        summary_lines=_summary_lines(
            source=source,
            target_id=target_id,
            total_count=len(fixtures),
            selected=selected,
            executable_count=len(executable_ids),
            blocked_count=len(blocked_ids),
            include_hints=include_hints,
        ),
    )


def _filter_fixtures(
    fixtures: Sequence[JailbreakBenchmarkFixture],
    *,
    fixture_ids: Sequence[str],
    families: Sequence[str],
) -> list[JailbreakBenchmarkFixture]:
    selected = list(fixtures)
    if fixture_ids:
        wanted = set(fixture_ids)
        selected = [fixture for fixture in selected if fixture.id in wanted]
    if families:
        wanted_families = set(families)
        selected = [fixture for fixture in selected if fixture.family in wanted_families]
    return selected


def _summary_lines(
    *,
    source: str,
    target_id: str,
    total_count: int,
    selected: Sequence[JailbreakBenchmarkFixture],
    executable_count: int,
    blocked_count: int,
    include_hints: bool,
) -> list[str]:
    lines = [
        "Benchmark dry-run: jailbreak corpus",
        f"Source: {source}",
        f"Target: {target_id}",
        f"Selected fixtures: {len(selected)} / {total_count}",
        f"Executable fixtures: {executable_count}",
        f"Blocked fixtures: {blocked_count}",
        "Evidence mode: metadata_only",
        "Raw prompt bodies: not loaded",
        "Target calls: not executed",
        "Scorecard: not scored (dry_run_no_execution)",
        "Promotion impact: none",
    ]
    for fixture in selected:
        status = "executable" if fixture.is_executable else "blocked"
        lines.append(
            f"- {fixture.id}: {fixture.family} -> {fixture.risk_plugin_id}/"
            f"{fixture.strategy_id} [{status}]"
        )
    if include_hints:
        lines.append("Hint profiles: included")
    return lines
