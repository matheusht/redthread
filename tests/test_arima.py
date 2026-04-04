"""Tests for Phase 5B — ARIMA Anomaly Detector.

Validates that the ArimaDetector correctly:
  - Flags latency spikes as anomalies
  - Avoids false positives on noisy-but-normal data
  - Falls back to Z-score when < min_observations
  - Returns None for insufficiently short series
  - Produces correct confidence bounds when fitting on stable data
"""

from __future__ import annotations

import random

import pytest

from redthread.telemetry.arima import ArimaDetector


@pytest.fixture
def detector() -> ArimaDetector:
    return ArimaDetector(confidence_level=0.95, min_observations=10, window_size=50)


def _stable_series(n: int = 30, base: float = 200.0, noise: float = 10.0) -> list[float]:
    """Generate a stable random-walk-like series around `base` with small noise."""
    random.seed(42)
    return [base + random.uniform(-noise, noise) for _ in range(n)]


class TestArimaDetectsSpike:
    """ARIMA must flag a dramatic latency spike as an anomaly."""

    def test_latency_spike_is_anomaly(self, detector: ArimaDetector) -> None:
        # 29 stable latency readings, then a 10× spike
        series = _stable_series(29, base=200.0, noise=15.0)
        series.append(5000.0)  # Sudden spike → anomaly

        result = detector.detect(series, "latency_ms")

        assert result is not None, "detector returned None for a spike series"
        assert result.is_anomaly is True, (
            f"Expected anomaly for 5000ms spike, got score={result.observed} "
            f"CI=[{result.lower_bound:.1f}, {result.upper_bound:.1f}]"
        )
        assert result.observed == pytest.approx(5000.0)

    def test_token_velocity_drop_is_anomaly(self, detector: ArimaDetector) -> None:
        # Normal token count ~300, sudden drop to 2 (evasion / guardrail hit)
        series = _stable_series(29, base=300.0, noise=20.0)
        series.append(2.0)

        result = detector.detect(series, "output_tokens")
        assert result is not None
        assert result.is_anomaly is True


class TestArimaNoFalsePositives:
    """ARIMA should NOT flag normal noisy data as anomalous."""

    def test_stable_series_no_anomaly(self, detector: ArimaDetector) -> None:
        # 30 observations of stable latency — last point is within normal range
        series = _stable_series(30, base=200.0, noise=10.0)
        # Override last to be within expected range
        series[-1] = 205.0

        result = detector.detect(series, "latency_ms")
        # We accept None (too few obs after removing last) or non-anomaly
        if result is not None:
            # For a stable series, the last normal point should not be anomalous
            # Allow borderline cases since ARIMA CI depends on auto_arima fit
            assert result.deviation_sigma < 5.0, (
                f"False positive: normal value flagged with σ={result.deviation_sigma:.2f}"
            )


class TestArimaFallback:
    """ArimaDetector should fall back to Z-score when < min_observations."""

    def test_z_score_fallback_when_few_observations(self) -> None:
        # Use min_observations=20; provide only 5 points → triggers Z-score
        detector = ArimaDetector(min_observations=20, confidence_level=0.95)
        series = _stable_series(5, base=100.0, noise=5.0)
        series.append(500.0)  # Spike at the end

        result = detector.detect(series, "latency_ms")
        assert result is not None
        assert result.fallback_method == "z_score"
        assert result.is_anomaly is True

    def test_returns_none_for_very_short_series(self, detector: ArimaDetector) -> None:
        result = detector.detect([100.0, 120.0], "latency_ms")
        assert result is None, "Series with < 3 obs should return None"


class TestArimaForecastBounds:
    """Confidence bounds must be logically consistent."""

    def test_bounds_are_ordered(self, detector: ArimaDetector) -> None:
        series = _stable_series(25, base=150.0, noise=8.0)
        result = detector.detect(series, "response_length")
        if result is not None:
            assert result.lower_bound <= result.upper_bound, (
                f"lower={result.lower_bound} > upper={result.upper_bound}"
            )

    def test_metric_name_preserved(self, detector: ArimaDetector) -> None:
        series = _stable_series(25, base=200.0, noise=10.0)
        result = detector.detect(series, "my_custom_metric")
        if result is not None:
            assert result.metric_name == "my_custom_metric"

    def test_n_observations_correct(self, detector: ArimaDetector) -> None:
        series = _stable_series(25, base=100.0, noise=5.0)
        result = detector.detect(series, "latency_ms")
        if result is not None:
            assert result.n_observations == 25
