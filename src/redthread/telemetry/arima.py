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
import warnings
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from redthread.telemetry.models import ArimaForecast

if TYPE_CHECKING:
    from redthread.telemetry.collector import TelemetryCollector

logger = logging.getLogger(__name__)

# Metrics that ARIMA monitors on the organic (non-canary) stream
MONITORED_METRICS = [
    "latency_ms",
    "output_tokens",
    "response_length",   # Derived: len(response_text) — added in collector
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
        arr = np.array(series, dtype=np.float64)
        mean = float(np.mean(arr))
        std = float(np.std(arr)) if len(arr) > 1 else 1.0
        observed = arr[-1]

        lower = mean - 2.0 * std
        upper = mean + 2.0 * std
        deviation_sigma = (observed - mean) / std if std > 0 else 0.0

        return ArimaForecast(
            metric_name=metric_name,
            observed=float(observed),
            predicted=mean,
            lower_bound=lower,
            upper_bound=upper,
            is_anomaly=bool(observed < lower or observed > upper),
            deviation_sigma=deviation_sigma,
            n_observations=len(series),
            fallback_method="z_score",
        )

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

        # Apply rolling window
        window = series[-self.window_size:]

        if len(window) < self.min_observations:
            logger.debug(
                "ArimaDetector | %s | %d obs < min %d — using Z-score fallback",
                metric_name, len(window), self.min_observations,
            )
            return self._z_score_fallback(window, metric_name)

        # Use all but the last point as training history; forecast the last.
        train = window[:-1]
        observed = window[-1]

        try:
            from pmdarima import auto_arima

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = auto_arima(
                    train,
                    stepwise=True,        # Faster grid search
                    suppress_warnings=True,
                    error_action="ignore",
                    max_p=3, max_q=3,     # Cap search space for speed
                    information_criterion="aic",
                )

            forecast_result = model.predict(n_periods=1, return_conf_int=True, alpha=1.0 - self.confidence_level)
            predicted_arr, conf_int = forecast_result
            predicted = float(predicted_arr[0])
            lower = float(conf_int[0][0])
            upper = float(conf_int[0][1])

            residuals = np.array(model.resid(), dtype=np.float64)
            std_err = float(np.std(residuals)) if len(residuals) > 1 else 1.0
            deviation_sigma = (observed - predicted) / std_err if std_err > 0 else 0.0

            result = ArimaForecast(
                metric_name=metric_name,
                observed=float(observed),
                predicted=predicted,
                lower_bound=lower,
                upper_bound=upper,
                is_anomaly=bool(observed < lower or observed > upper),
                deviation_sigma=deviation_sigma,
                n_observations=len(window),
                fallback_method="",
            )

            if result.is_anomaly:
                logger.warning(
                    "🚨 ArimaDetector | ANOMALY | metric=%s | observed=%.2f | "
                    "predicted=%.2f | CI=[%.2f, %.2f] | σ=%.2f",
                    metric_name, observed, predicted, lower, upper, deviation_sigma,
                )
            else:
                logger.debug(
                    "ArimaDetector | metric=%s | ok | observed=%.2f | CI=[%.2f, %.2f]",
                    metric_name, observed, lower, upper,
                )

            return result

        except Exception as exc:
            logger.warning(
                "ArimaDetector | %s | auto_arima failed (%s) — Z-score fallback",
                metric_name, exc,
            )
            return self._z_score_fallback(window, metric_name)

    def analyze_collector(
        self, collector: "TelemetryCollector"
    ) -> list[ArimaForecast]:
        """Run anomaly detection across all monitored metric streams.

        Derives response_length from response_text on the fly.
        Returns a list of ArimaForecast — one per metric with sufficient data.
        """
        forecasts: list[ArimaForecast] = []
        organic_records = collector.get_organic_records(window=self.window_size)

        # latency_ms and output_tokens come directly from collector
        for metric in ("latency_ms", "output_tokens"):
            series = collector.get_metric_series(metric, window=self.window_size)
            if series:
                result = self.detect(series, metric)
                if result is not None:
                    forecasts.append(result)

        # response_length is derived from response_text
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
