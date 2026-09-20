"""ArimaDetector — Phase 5B: Time-Series Anomaly Detection.

The heart-rate monitor. Fits an ARIMA model to each metric stream and
flags observations outside the confidence interval as anomalies.

Uses pmdarima.auto_arima for automatic (p,d,q) order selection — this
prevents the silent false negatives that arise from hardcoding a fixed
ARIMA(1,1,1) order in environments with different baseline behaviors.

Monitored metrics:
  - latency_ms       → Response time spikes (model degradation or injection)
  - output_tokens    → Token velocity changes (evasion or policy drift)
  - response_length  → Character count (sudden terseness or verbosity)

Fallback: Z-score (±2σ) when fewer than min_observations records exist.
"""

from __future__ import annotations

import logging

import numpy as np

from redthread.telemetry.arima_helpers import (
    compute_z_score_fallback,
    constant_forecast,
    fit_arima_prediction,
)
from redthread.telemetry.collector import TelemetryCollector
from redthread.telemetry.models import ArimaForecast

logger = logging.getLogger(__name__)

MONITORED_METRICS = [
    "latency_ms",
    "output_tokens",
    "response_length",
]


class ArimaDetector:
    """ARIMA-based anomaly detection on operational metric time-series.

    For each monitored metric, fits auto_arima to the historical series
    and flags the latest observation as anomalous if it falls outside
    the (confidence_level) prediction interval.
    """

    def __init__(
        self,
        confidence_level: float = 0.95,
        min_observations: int = 20,
        window_size: int = 50,
    ) -> None:
        self.confidence_level = confidence_level
        self.min_observations = min_observations
        self.window_size = window_size

    def _z_score_fallback(
        self, series: list[float], metric_name: str
    ) -> ArimaForecast:
        """Fallback when < min_observations. Uses ±2σ Z-score detection."""
        return compute_z_score_fallback(series, metric_name)

    def detect(self, series: list[float], metric_name: str) -> ArimaForecast | None:
        """Fit ARIMA to the historical series and flag the latest observation.

        Returns None if the series is empty or has fewer than 3 observations.
        Uses Z-score fallback for series shorter than min_observations.

        Args:
            series: Chronologically ordered metric values.
            metric_name: Human-readable metric label.
        """
        if len(series) < 3:
            logger.debug("ArimaDetector | %s | too few points (%d) — skipping", metric_name, len(series))
            return None

        window = series[-self.window_size:]

        if float(np.var(window)) < 1e-9:
            return constant_forecast(window, metric_name)

        if len(window) < self.min_observations:
            logger.debug(
                "ArimaDetector | %s | %d obs < min %d — using Z-score fallback",
                metric_name, len(window), self.min_observations,
            )
            return self._z_score_fallback(window, metric_name)

        train = window[:-1]
        observed = window[-1]

        try:
            result = fit_arima_prediction(
                train=train,
                observed=observed,
                confidence_level=self.confidence_level,
                window_len=len(window),
                metric_name=metric_name,
            )

            if result.is_anomaly:
                logger.warning(
                    "🚨 ArimaDetector | ANOMALY | metric=%s | observed=%.2f | "
                    "predicted=%.2f | CI=[%.2f, %.2f] | σ=%.2f",
                    metric_name,
                    observed,
                    result.predicted,
                    result.lower_bound,
                    result.upper_bound,
                    result.deviation_sigma,
                )
            else:
                logger.debug(
                    "ArimaDetector | metric=%s | ok | observed=%.2f | CI=[%.2f, %.2f]",
                    metric_name,
                    observed,
                    result.lower_bound,
                    result.upper_bound,
                )

            return result

        except Exception as exc:
            logger.warning(
                "ArimaDetector | %s | auto_arima failed (%s) — Z-score fallback",
                metric_name, exc,
            )
            return self._z_score_fallback(window, metric_name)

    def analyze_collector(
        self, collector: TelemetryCollector
    ) -> list[ArimaForecast]:
        """Run anomaly detection across all monitored metric streams.

        Derives response_length from response_text on the fly.
        Returns a list of ArimaForecast — one per metric with sufficient data.
        """
        forecasts: list[ArimaForecast] = []
        organic_records = collector.get_organic_records(window=self.window_size)

        for metric in ("latency_ms", "output_tokens"):
            series = collector.get_metric_series(metric, window=self.window_size)
            if series:
                result = self.detect(series, metric)
                if result is not None:
                    forecasts.append(result)

        lengths = [len(r.response_text) for r in organic_records]
        if lengths:
            result = self.detect(lengths, "response_length")
            if result is not None:
                forecasts.append(result)

        anomaly_count = sum(1 for f in forecasts if f.is_anomaly)
        logger.info(
            "📊 ArimaDetector | checked %d metrics | %d anomalies detected",
            len(forecasts), anomaly_count,
        )
        return forecasts
