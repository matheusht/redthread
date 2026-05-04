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
    UNSCORED_EVIDENCE_REASONS,
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


def test_every_evidence_mode_has_explicit_score_contract() -> None:
    expected_caps = {
        BenchmarkEvidenceMode.METADATA_ONLY: 0,
        BenchmarkEvidenceMode.WEAK_IMPORTED_EVIDENCE: 0,
        BenchmarkEvidenceMode.SEALED_LOCAL_REPLAY: 0,
        BenchmarkEvidenceMode.SEALED_RUNTIME_REVIEW: 25,
        BenchmarkEvidenceMode.JUDGE_CONFIRMED_SANDBOX: 100,
        BenchmarkEvidenceMode.DEFENSE_VALIDATED: 100,
    }

    assert set(expected_caps) == set(BenchmarkEvidenceMode)
    assert set(UNSCORED_EVIDENCE_REASONS) == {
        BenchmarkEvidenceMode.METADATA_ONLY,
        BenchmarkEvidenceMode.WEAK_IMPORTED_EVIDENCE,
        BenchmarkEvidenceMode.SEALED_LOCAL_REPLAY,
    }
    for evidence_mode, cap in expected_caps.items():
        assert evidence_mode_score_cap(evidence_mode) == cap


def test_every_not_scored_reason_builds_zero_scorecard() -> None:
    for reason in BenchmarkNotScoredReason:
        scorecard = build_unscored_scorecard(
            lane=BenchmarkLane.JAILBREAK,
            source="contract-test",
            target_id="local-dev",
            evidence_mode=BenchmarkEvidenceMode.METADATA_ONLY,
            run_mode=BenchmarkRunMode.DRY_RUN,
            promotion_impact=BenchmarkPromotionImpact.NONE,
            not_scored_reason=reason,
        )

        assert scorecard.total_score == 0
        assert scorecard.not_scored_reason == reason
        assert scorecard.is_scored is False


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
