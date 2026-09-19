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

    def _insufficient_data_report(
        self, collector: TelemetryCollector, required_records: int
    ) -> ASIReport:
        available_records = collector.total_records
        warning = (
            f"Insufficient telemetry records ({available_records}/{required_records}); "
            "ASI uses a neutral score until the minimum window is available."
        )
        organic_records = collector.get_organic_records()
        canary_records = collector.get_canary_records()
        canary_history = any(
            sum(1 for record in canary_records if record.canary_id == canary_id and record.response_embedding) >= 2
            for canary_id in {record.canary_id for record in canary_records}
        )
        response_mode = "measured" if canary_history else "no_canaries" if not canary_records else "insufficient_canary_history"
        semantic_mode = "no_baseline" if self._drift_detector._baseline_embeddings is None else (
            "measured" if any(record.response_embedding for record in organic_records) else "no_organic_embeddings"
        )
        evidence_warnings = []
        if response_mode != "measured":
            evidence_warnings.append("Response Consistency defaulted high because canary history is missing or too thin.")
        if semantic_mode == "no_baseline":
            evidence_warnings.append("Semantic Drift defaulted high because no benign baseline is fitted.")
        elif semantic_mode == "no_organic_embeddings":
            evidence_warnings.append("Semantic Drift defaulted high because no organic response embeddings were available.")
        if available_records == collector.total_canary_records and available_records > 0:
            evidence_warnings.append("Current telemetry is canary-only. It is useful for operator monitoring, not proof of full benign utility.")
        evidence_warnings.append(warning)
        metadata = {
            "status": "insufficient_data", "organic_records": len(organic_records),
            "canary_records": collector.total_canary_records,
            "baseline_fitted": self._drift_detector._baseline_embeddings is not None,
            "response_consistency_mode": response_mode,
            "semantic_drift_mode": semantic_mode,
            "evidence_warnings": evidence_warnings,
            "insufficient_data_warning": warning,
        }
        report = ASIReport(
            target_model=self.settings.target_model,
            window_size=min(available_records, required_records),
            status="insufficient_data",
            overall_score=100.0,
            response_consistency=100.0,
            semantic_drift=100.0,
            operational_health=100.0,
            behavioral_stability=100.0,
            anomalies=[],
            is_alert=False,
            alert_threshold=self.settings.asi_alert_threshold,
            recommendation="",
            metadata=metadata,
        )
        return report.model_copy(update={"recommendation": generate_recommendation(report)})

    def compute(self, collector: TelemetryCollector) -> ASIReport:
        """Compute a truth-aware ASI report from collector data."""
        record_count = collector.total_records
        organic_records = collector.get_organic_records()
        logger.info(
            "🧠 ASI | computing health score | records=%d (organic=%d, canary=%d)",
            record_count,
            len(organic_records),
            collector.total_canary_records,
        )
        if record_count < self.settings.asi_window_size:
            return self._insufficient_data_report(collector, self.settings.asi_window_size)

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
        metadata["status"] = "ok"
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
