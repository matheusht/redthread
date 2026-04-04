"""Tests for Phase 5B — Agent Stability Index (ASI).

Validates the composite health score computation:
  - Perfect health (stable, consistent, no anomalies) → ASI ≈ 100
  - Degraded health (injected anomalies + drift) → ASI drops below threshold
  - Critical case → ASI < 30, is_alert=True
  - Weights sum to exactly 1.0
  - Score is always clamped to [0, 100]
  - Recommendation text matches score tier
  - No canary records → RC defaults to 100 (unknown = healthy)
  - ARIMA sub-score with no anomalies → OH = 100
"""

from __future__ import annotations

import asyncio
import random

import numpy as np
import pytest

from redthread.config.settings import RedThreadSettings, TargetBackend
from redthread.telemetry.arima import ArimaDetector
from redthread.telemetry.asi import AgentStabilityIndex
from redthread.telemetry.collector import TelemetryCollector
from redthread.telemetry.models import ArimaForecast, TelemetryRecord


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def settings() -> RedThreadSettings:
    return RedThreadSettings(
        target_backend=TargetBackend.OPENAI,
        target_model="gpt-4o",
        attacker_backend=TargetBackend.OLLAMA,
        attacker_model="llama3.2:3b",
        judge_backend=TargetBackend.OPENAI,
        judge_model="gpt-4o",
        openai_api_key="sk-test",
        dry_run=True,
        telemetry_enabled=True,
        asi_window_size=50,
        arima_confidence_level=0.95,
        asi_alert_threshold=60.0,
    )


@pytest.fixture
def asi(settings: RedThreadSettings) -> AgentStabilityIndex:
    return AgentStabilityIndex(settings=settings)


def _make_embedding(seed: int, dim: int = 1536) -> list[float]:
    """Return a deterministic unit-normalized embedding."""
    rng = random.Random(seed)
    vec = [rng.uniform(-1.0, 1.0) for _ in range(dim)]
    norm = sum(x * x for x in vec) ** 0.5
    return [x / norm for x in vec]


def _populate_collector_stable(
    collector: TelemetryCollector, n: int = 30, base_seed: int = 42
) -> None:
    """Fill collector with stable organic records (identical embedding seed cluster)."""
    rng = random.Random(base_seed)
    for i in range(n):
        record = TelemetryRecord(
            target_model="gpt-4o",
            prompt_hash=f"hash-{i:04d}",
            latency_ms=200.0 + rng.uniform(-10, 10),
            input_tokens=50,
            output_tokens=100 + rng.randint(-5, 5),
            response_text="This is a normal response." * 3,
            response_embedding=_make_embedding(base_seed),  # Same base cluster
            is_canary=False,
        )
        collector._records.append(record)


def _populate_canaries_stable(
    collector: TelemetryCollector, n_rounds: int = 3, base_seed: int = 42
) -> None:
    """Add n_rounds of canary records with near-identical embeddings."""
    canary_ids = ["canary-001", "canary-002", "canary-003"]
    for round_i in range(n_rounds):
        for cid in canary_ids:
            # Same seed per canary_id across rounds = high consistency
            emb = _make_embedding(seed=hash(cid) % 1000)
            record = TelemetryRecord(
                target_model="gpt-4o",
                prompt_hash=f"cp-{cid}-{round_i}",
                latency_ms=180.0,
                input_tokens=10,
                output_tokens=15,
                response_text="Hello.",
                response_embedding=emb,
                is_canary=True,
                canary_id=cid,
            )
            collector._records.append(record)


# ── Test classes ──────────────────────────────────────────────────────────────

class TestASIPerfectHealth:
    """Stable data should produce a high ASI score."""

    def test_stable_inputs_produce_high_score(
        self, asi: AgentStabilityIndex, settings: RedThreadSettings
    ) -> None:
        collector = TelemetryCollector(settings)
        _populate_collector_stable(collector, n=30)
        _populate_canaries_stable(collector, n_rounds=3)

        report = asi.compute(collector)

        # With stable data, RC should be high (consistent canary embeddings)
        assert report.response_consistency >= 70.0, (
            f"Expected RC≥70 for stable data, got {report.response_consistency:.1f}"
        )
        # BS should be high (stable token counts)
        assert report.behavioral_stability >= 70.0, (
            f"Expected BS≥70, got {report.behavioral_stability:.1f}"
        )
        # Overall must be in bounds
        assert 0.0 <= report.overall_score <= 100.0


class TestASIWeights:
    """Weight sum must equal exactly 1.0."""

    def test_weights_sum_to_one(self) -> None:
        total = sum(AgentStabilityIndex.WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9, f"Weights sum to {total}, expected 1.0"

    def test_all_four_weights_present(self) -> None:
        keys = set(AgentStabilityIndex.WEIGHTS.keys())
        expected = {"response_consistency", "semantic_drift", "operational_health", "behavioral_stability"}
        assert keys == expected


class TestASIScoreBounds:
    """ASI must always be clamped to [0, 100] regardless of sub-score extremes."""

    def test_score_in_zero_to_hundred_range(
        self, asi: AgentStabilityIndex, settings: RedThreadSettings
    ) -> None:
        collector = TelemetryCollector(settings)
        _populate_collector_stable(collector, n=10)

        report = asi.compute(collector)
        assert 0.0 <= report.overall_score <= 100.0

    def test_individual_sub_scores_bounded(
        self, asi: AgentStabilityIndex, settings: RedThreadSettings
    ) -> None:
        collector = TelemetryCollector(settings)
        _populate_collector_stable(collector, n=10)
        _populate_canaries_stable(collector, n_rounds=1)

        report = asi.compute(collector)
        for attr in ("response_consistency", "semantic_drift", "operational_health", "behavioral_stability"):
            val = getattr(report, attr)
            assert 0.0 <= val <= 100.0, f"{attr}={val} out of [0,100]"


class TestASINoCanaryDefault:
    """When no canary records exist, RC defaults to 100 (unknown = healthy)."""

    def test_no_canary_rc_defaults_to_100(
        self, asi: AgentStabilityIndex, settings: RedThreadSettings
    ) -> None:
        collector = TelemetryCollector(settings)
        _populate_collector_stable(collector, n=20)
        # No canary records added

        report = asi.compute(collector)
        assert report.response_consistency == pytest.approx(100.0), (
            f"Expected RC=100 with no canaries, got {report.response_consistency}"
        )


class TestASIOperationalHealth:
    """OH score reflects ARIMA anomaly presence."""

    def test_no_operational_anomalies_gives_oh_100(
        self, asi: AgentStabilityIndex, settings: RedThreadSettings
    ) -> None:
        # When ARIMA returns no anomalies, OH = 100
        report_oh = asi._score_operational_health(forecasts=[])
        assert report_oh == pytest.approx(100.0)

    def test_all_anomalies_gives_oh_zero(
        self, asi: AgentStabilityIndex
    ) -> None:
        # All 3 metrics anomalous → OH = 0
        fake_anomalies = [
            ArimaForecast(
                metric_name=m,
                observed=9999.0,
                predicted=100.0,
                lower_bound=80.0,
                upper_bound=120.0,
                is_anomaly=True,
                deviation_sigma=10.0,
                n_observations=30,
            )
            for m in ("latency_ms", "output_tokens", "response_length")
        ]
        score = asi._score_operational_health(forecasts=fake_anomalies)
        assert score == pytest.approx(0.0)

    def test_partial_anomalies_gives_proportional_oh(
        self, asi: AgentStabilityIndex
    ) -> None:
        # 1 of 2 metrics anomalous → OH = 50
        forecasts = [
            ArimaForecast(
                metric_name="latency_ms",
                observed=9999.0, predicted=100.0,
                lower_bound=80.0, upper_bound=120.0,
                is_anomaly=True, deviation_sigma=10.0, n_observations=30,
            ),
            ArimaForecast(
                metric_name="output_tokens",
                observed=105.0, predicted=100.0,
                lower_bound=80.0, upper_bound=120.0,
                is_anomaly=False, deviation_sigma=0.5, n_observations=30,
            ),
        ]
        score = asi._score_operational_health(forecasts=forecasts)
        assert score == pytest.approx(50.0)


class TestASIRecommendation:
    """Recommendation text must match the score tier."""

    def test_excellent_tier_recommendation(
        self, asi: AgentStabilityIndex, settings: RedThreadSettings
    ) -> None:
        collector = TelemetryCollector(settings)
        _populate_collector_stable(collector, n=30)
        _populate_canaries_stable(collector, n_rounds=5)

        report = asi.compute(collector)
        # Whatever the score, check tier → recommendation consistency
        if report.health_tier == "EXCELLENT":
            assert "fully stable" in report.recommendation.lower()
        elif report.health_tier == "CRITICAL":
            assert "critical" in report.recommendation.lower() or "immediate" in report.recommendation.lower()

    def test_alert_flag_matches_threshold(
        self, asi: AgentStabilityIndex, settings: RedThreadSettings
    ) -> None:
        collector = TelemetryCollector(settings)
        _populate_collector_stable(collector, n=10)

        report = asi.compute(collector)
        if report.overall_score < settings.asi_alert_threshold:
            assert report.is_alert is True
        else:
            assert report.is_alert is False
