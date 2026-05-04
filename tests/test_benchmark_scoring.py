"""Tests for deterministic benchmark scorecard helpers."""

from __future__ import annotations

from redthread.benchmarks.models import (
    BenchmarkEvidenceMode,
    BenchmarkLane,
    BenchmarkNotScoredReason,
    BenchmarkPromotionImpact,
    BenchmarkRunMode,
)
from redthread.benchmarks.scoring import (
    SCORE_DIMENSION_WEIGHTS,
    build_unscored_scorecard,
    evidence_mode_score_cap,
    score_confirmed_benchmark,
)


def test_score_dimension_weights_sum_to_100() -> None:
    assert sum(SCORE_DIMENSION_WEIGHTS.values()) == 100


def test_metadata_only_scorecard_is_explicitly_unscored() -> None:
    scorecard = build_unscored_scorecard(
        lane=BenchmarkLane.JAILBREAK,
        source="spiritual-spell",
        target_id="local-dev",
        evidence_mode=BenchmarkEvidenceMode.METADATA_ONLY,
        run_mode=BenchmarkRunMode.DRY_RUN,
        promotion_impact=BenchmarkPromotionImpact.NONE,
        not_scored_reason=BenchmarkNotScoredReason.DRY_RUN_NO_EXECUTION,
        fixture_ids=["spiritual-spell-0032"],
        denominator=1,
        blocked_count=1,
    )

    assert scorecard.total_score == 0
    assert scorecard.not_scored_reason == BenchmarkNotScoredReason.DRY_RUN_NO_EXECUTION
    assert scorecard.is_scored is False


def test_weak_and_sealed_evidence_have_zero_score_cap() -> None:
    assert evidence_mode_score_cap(BenchmarkEvidenceMode.WEAK_IMPORTED_EVIDENCE) == 0
    assert evidence_mode_score_cap(BenchmarkEvidenceMode.SEALED_LOCAL_REPLAY) == 0


def test_confirmed_scorecard_is_deterministic_and_capped() -> None:
    scorecard = score_confirmed_benchmark(
        lane=BenchmarkLane.JAILBREAK,
        source="spiritual-spell",
        target_id="local-dev",
        evidence_mode=BenchmarkEvidenceMode.JUDGE_CONFIRMED_SANDBOX,
        run_mode=BenchmarkRunMode.SANDBOX_REPLAY,
        promotion_impact=BenchmarkPromotionImpact.REGRESSION_CANDIDATE,
        dimension_points={name: 999 for name in SCORE_DIMENSION_WEIGHTS},
        fixture_ids=["spiritual-spell-0032"],
        denominator=1,
    )

    assert scorecard.total_score == 100
    assert scorecard.is_scored is True
    assert len(scorecard.dimensions) == len(SCORE_DIMENSION_WEIGHTS)


def test_unscored_evidence_cannot_be_converted_to_confirmed_points() -> None:
    scorecard = score_confirmed_benchmark(
        lane=BenchmarkLane.JAILBREAK,
        source="promptfoo",
        target_id="local-dev",
        evidence_mode=BenchmarkEvidenceMode.WEAK_IMPORTED_EVIDENCE,
        run_mode=BenchmarkRunMode.DRY_RUN,
        promotion_impact=BenchmarkPromotionImpact.NONE,
        dimension_points={"severity_harm_potential": 20},
    )

    assert scorecard.total_score == 0
    assert scorecard.not_scored_reason == BenchmarkNotScoredReason.WEAK_IMPORTED_EVIDENCE
