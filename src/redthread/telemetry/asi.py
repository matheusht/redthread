"""AgentStabilityIndex — composite telemetry health score."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from redthread.config.settings import RedThreadSettings
from redthread.telemetry.arima import ArimaDetector
from redthread.telemetry.assessment import (
    build_report_metadata,
    generate_recommendation,
    score_behavioral_stability,
    score_operational_health,
    score_response_consistency,
    score_semantic_drift,
)
from redthread.telemetry.drift import DriftDetector
from redthread.telemetry.models import ASIReport

if TYPE_CHECKING:
    from redthread.telemetry.collector import TelemetryCollector

logger = logging.getLogger(__name__)


class AgentStabilityIndex:
    """Compute the ASI health score.

    ASI is an operator signal, not proof of safety or utility.
    Missing telemetry evidence currently defaults some sub-scores high,
    so reports must carry evidence caveats.
    """

    WEIGHTS: dict[str, float] = {
        "response_consistency": 0.30,
        "semantic_drift": 0.30,
        "operational_health": 0.25,
        "behavioral_stability": 0.15,
    }

    def __init__(
        self,
        settings: RedThreadSettings,
        drift_detector: DriftDetector | None = None,
    ) -> None:
        self.settings = settings
        self._drift_detector = drift_detector or DriftDetector(k_neighbors=5, distance_metric="cosine")
        self._arima_detector = ArimaDetector(
            confidence_level=settings.arima_confidence_level,
            min_observations=20,
            window_size=settings.asi_window_size,
        )

    def _weighted_score(self, rc: float, sd: float, oh: float, bs: float) -> float:
        weights = self.WEIGHTS
        overall = (
            weights["response_consistency"] * rc
            + weights["semantic_drift"] * sd
            + weights["operational_health"] * oh
            + weights["behavioral_stability"] * bs
        )
        return max(0.0, min(100.0, overall))

    def _score_operational_health(self, forecasts: list) -> float:
        """Backward-compatible wrapper for focused tests."""
        return score_operational_health(forecasts)[0]

    def _score_behavioral_stability(self, collector: TelemetryCollector) -> float:
        """Backward-compatible wrapper for focused tests."""
        return score_behavioral_stability(collector, self.settings.asi_window_size)[0]

    def compute(self, collector: TelemetryCollector) -> ASIReport:
        """Compute a truth-aware ASI report from collector data."""
        organic_records = collector.get_organic_records()
        logger.info(
            "🧠 ASI | computing health score | records=%d (organic=%d, canary=%d)",
            collector.total_records,
            len(organic_records),
            collector.total_canary_records,
        )

        forecasts = self._arima_detector.analyze_collector(collector)
        rc, rc_mode = score_response_consistency(collector)
        sd, sd_mode = score_semantic_drift(
            collector,
            self._drift_detector,
            self.settings.asi_window_size,
        )
        oh, oh_mode = score_operational_health(forecasts)
        bs, bs_mode = score_behavioral_stability(collector, self.settings.asi_window_size)
        overall = self._weighted_score(rc, sd, oh, bs)
        metadata = build_report_metadata(
            collector,
            self._drift_detector,
            forecasts,
            {
                "response_consistency": rc_mode,
                "semantic_drift": sd_mode,
                "operational_health": oh_mode,
                "behavioral_stability": bs_mode,
            },
        )
        report = ASIReport(
            target_model=self.settings.target_model,
            window_size=min(collector.total_records, self.settings.asi_window_size),
            overall_score=overall,
            response_consistency=rc,
            semantic_drift=sd,
            operational_health=oh,
            behavioral_stability=bs,
            anomalies=forecasts,
            is_alert=overall < self.settings.asi_alert_threshold,
            alert_threshold=self.settings.asi_alert_threshold,
            recommendation="",
            metadata=metadata,
        )
        report = report.model_copy(update={"recommendation": generate_recommendation(report)})

        logger.info(
            "🧠 ASI | score=%.1f [%s] | RC=%.0f SD=%.0f OH=%.0f BS=%.0f | alert=%s",
            overall,
            report.health_tier,
            rc,
            sd,
            oh,
            bs,
            report.is_alert,
        )
        if report.is_alert:
            logger.warning(
                "🚨 ASI ALERT | score=%.1f below threshold=%.1f | %s",
                overall,
                self.settings.asi_alert_threshold,
                report.recommendation,
            )
        return report
