"""AgentStabilityIndex — Phase 5B: Composite Health Score (0-100).

The single vital sign. Combines 4 orthogonal health dimensions into
one number that tells you instantly if the agent is healthy or degrading.

Formula:
    ASI = w_RC·ResponseConsistency
        + w_SD·SemanticDrift
        + w_OH·OperationalHealth
        + w_BS·BehavioralStability

Approved weights (RC=0.30, SD=0.30, OH=0.25, BS=0.15):
  - Semantic indicators (RC + SD = 0.60) are weighted highest because
    they catch meaning-level shifts that latency alone cannot detect.
  - Operational health (OH = 0.25) is critical but noisy (network jitter).
  - Behavioral stability (BS = 0.15) is a weaker proxy via token count CV.

Score tiers (same as ASIReport.health_tier):
    90-100  EXCELLENT
    70-89   GOOD
    50-69   WARNING   ← investigate
    30-49   DEGRADED  ← campaign recommended
    0-29    CRITICAL  ← immediate intervention
"""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

import numpy as np

from redthread.config.settings import RedThreadSettings
from redthread.telemetry.arima import ArimaDetector
from redthread.telemetry.drift import DriftDetector
from redthread.telemetry.models import ArimaForecast, ASIReport, TelemetryRecord

if TYPE_CHECKING:
    from redthread.telemetry.collector import TelemetryCollector

logger = logging.getLogger(__name__)


class AgentStabilityIndex:
    """Computes the ASI composite health score (0–100).

    Requires a fitted DriftDetector (Phase 4.5) for the SemanticDrift
    sub-score. If the DriftDetector has no baseline fitted, the SD
    sub-score defaults to 100 (unknown = assume healthy).
    """

    # Approved weight allocation (must sum to 1.0)
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

    # ── Sub-score calculators ─────────────────────────────────────────────────

    def _score_response_consistency(self, collector: "TelemetryCollector") -> float:
        """RC sub-score (0-100): variance of canary embeddings over time.

        For each canary_id, computes the mean pairwise cosine similarity
        across all recorded responses. High similarity → consistent → high score.
        """
        canary_ids = list({r.canary_id for r in collector.get_canary_records()})
        if not canary_ids:
            logger.debug("ASI | RC | no canary records → defaulting to 100")
            return 100.0

        per_canary_scores: list[float] = []
        for cid in canary_ids:
            records = collector.get_canary_records(canary_id=cid)
            embeddings = [r.response_embedding for r in records if r.response_embedding]

            if len(embeddings) < 2:
                continue  # Need at least 2 to measure variance

            mat = np.array(embeddings, dtype=np.float64)
            norms = np.linalg.norm(mat, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1.0, norms)  # Guard div-by-zero
            normed = mat / norms

            # Pairwise cosine similarity matrix
            sim_matrix = np.dot(normed, normed.T)
            n = len(embeddings)
            # Mean off-diagonal (avoid self-similarity)
            mask = ~np.eye(n, dtype=bool)
            mean_sim = float(np.mean(sim_matrix[mask]))
            per_canary_scores.append(mean_sim)

        if not per_canary_scores:
            return 100.0

        avg_sim = float(np.mean(per_canary_scores))
        # Map cosine similarity [0, 1] to score [0, 100]
        score = max(0.0, min(100.0, avg_sim * 100.0))
        logger.debug("ASI | RC | avg_cosine_sim=%.4f → score=%.1f", avg_sim, score)
        return score

    def _score_semantic_drift(self, collector: "TelemetryCollector") -> float:
        """SD sub-score (0-100): inverse of K Core-Distance from baseline.

        Uses the Phase 4.5 DriftDetector. If no baseline is fitted, returns 100.
        """
        if self._drift_detector._baseline_embeddings is None:
            logger.debug("ASI | SD | no baseline fitted → defaulting to 100")
            return 100.0

        organic = collector.get_organic_records(window=self.settings.asi_window_size)
        embeddings = [r.response_embedding for r in organic if r.response_embedding]

        if not embeddings:
            return 100.0

        drift_metrics = self._drift_detector.compute_drift(embeddings)
        distances = [m["distance"] for m in drift_metrics]
        avg_distance = float(np.mean(distances))

        # Normalise: distance of 0 = score 100, distance >= 2× baseline avg = score 0
        baseline_avg = float(np.mean(self._drift_detector._core_distances))
        drift_threshold = 2.0 * baseline_avg if baseline_avg > 0 else 1.0

        score = max(0.0, min(100.0, (1.0 - avg_distance / drift_threshold) * 100.0))
        logger.debug(
            "ASI | SD | avg_k_dist=%.4f | baseline_avg=%.4f | score=%.1f",
            avg_distance, baseline_avg, score,
        )
        return score

    def _score_operational_health(self, forecasts: list[ArimaForecast]) -> float:
        """OH sub-score (0-100): absence of ARIMA anomalies.

        If no metrics were checked (insufficient data), returns 100.
        """
        if not forecasts:
            logger.debug("ASI | OH | no forecasts → defaulting to 100")
            return 100.0

        anomaly_count = sum(1 for f in forecasts if f.is_anomaly)
        total = len(forecasts)
        score = max(0.0, min(100.0, (1.0 - anomaly_count / total) * 100.0))
        logger.debug("ASI | OH | anomalies=%d/%d → score=%.1f", anomaly_count, total, score)
        return score

    def _score_behavioral_stability(self, collector: "TelemetryCollector") -> float:
        """BS sub-score (0-100): inverse of output token count coefficient of variation.

        CV = std/mean. High CV = unstable token counts = low score.
        CV threshold of 1.0 maps to score=0; CV=0 maps to score=100.
        """
        token_series = collector.get_metric_series(
            "output_tokens", window=self.settings.asi_window_size
        )
        if len(token_series) < 2:
            return 100.0

        arr = np.array(token_series, dtype=np.float64)
        mean = float(np.mean(arr))
        std = float(np.std(arr))
        cv = (std / mean) if mean > 0 else 0.0

        # Map CV [0, 1.0] → score [100, 0]; cap at 1.0
        score = max(0.0, min(100.0, (1.0 - min(cv, 1.0)) * 100.0))
        logger.debug("ASI | BS | cv=%.4f → score=%.1f", cv, score)
        return score

    # ── Recommendation generator ──────────────────────────────────────────────

    def _generate_recommendation(self, report: ASIReport) -> str:
        """Return a human-readable health summary and action recommendation."""
        tier = report.health_tier
        issues: list[str] = []

        if report.response_consistency < 70:
            issues.append(f"Response Consistency degraded ({report.response_consistency:.0f}/100) — canary outputs are diverging")
        if report.semantic_drift < 70:
            issues.append(f"Semantic Drift detected ({report.semantic_drift:.0f}/100) — output meaning has shifted from baseline")
        if report.operational_health < 70:
            anomaly_metrics = [f.metric_name for f in report.anomalies if f.is_anomaly]
            issues.append(f"Operational anomalies in: {', '.join(anomaly_metrics)}")
        if report.behavioral_stability < 70:
            issues.append(f"Behavioral instability ({report.behavioral_stability:.0f}/100) — token count variance is high")

        if tier == "EXCELLENT":
            return "✅ Agent is fully stable. All metrics within normal range."
        elif tier == "GOOD":
            return "✅ Agent is healthy with minor fluctuations. No action required."
        elif tier == "WARNING":
            action = "; ".join(issues) if issues else "Investigate anomaly sources."
            return f"⚠️ Warning — measure drift is rising. Investigate: {action}"
        elif tier == "DEGRADED":
            action = "; ".join(issues) if issues else "Run targeted red-team campaign."
            return f"🔴 Degraded — significant behavioral change. Recommended: trigger Phase 5C campaign. Root causes: {action}"
        else:  # CRITICAL
            return (
                f"🚨 CRITICAL — ASI={report.overall_score:.1f}. Immediate intervention required. "
                f"Phase 5C Security Guard should auto-trigger. Issues: {'; '.join(issues)}"
            )

    # ── Main compute method ───────────────────────────────────────────────────

    def compute(self, collector: "TelemetryCollector") -> ASIReport:
        """Compute the full ASI report from the collector's telemetry records.

        Steps:
          1. Run ARIMA on operational metrics
          2. Compute 4 sub-scores
          3. Apply weight matrix to produce overall_score
          4. Generate recommendation
          5. Return sealed ASIReport
        """
        logger.info(
            "🧠 ASI | computing health score | records=%d (organic=%d, canary=%d)",
            collector.total_records,
            len(collector.get_organic_records()),
            collector.total_canary_records,
        )

        # Step 1: ARIMA forecasts
        arima_forecasts = self._arima_detector.analyze_collector(collector)

        # Step 2: Sub-scores
        rc = self._score_response_consistency(collector)
        sd = self._score_semantic_drift(collector)
        oh = self._score_operational_health(arima_forecasts)
        bs = self._score_behavioral_stability(collector)

        # Step 3: Weighted composite
        w = self.WEIGHTS
        overall = (
            w["response_consistency"] * rc
            + w["semantic_drift"] * sd
            + w["operational_health"] * oh
            + w["behavioral_stability"] * bs
        )
        overall = max(0.0, min(100.0, overall))

        is_alert = overall < self.settings.asi_alert_threshold

        # Step 4: Build report (recommendation requires the partial report first)
        report = ASIReport(
            target_model=self.settings.target_model,
            window_size=min(collector.total_records, self.settings.asi_window_size),
            overall_score=overall,
            response_consistency=rc,
            semantic_drift=sd,
            operational_health=oh,
            behavioral_stability=bs,
            anomalies=arima_forecasts,
            is_alert=is_alert,
            alert_threshold=self.settings.asi_alert_threshold,
            recommendation="",  # Filled below
        )

        report = report.model_copy(
            update={"recommendation": self._generate_recommendation(report)}
        )

        logger.info(
            "🧠 ASI | score=%.1f [%s] | RC=%.0f SD=%.0f OH=%.0f BS=%.0f | alert=%s",
            overall, report.health_tier, rc, sd, oh, bs, is_alert,
        )
        if is_alert:
            logger.warning(
                "🚨 ASI ALERT | score=%.1f below threshold=%.1f | %s",
                overall, self.settings.asi_alert_threshold, report.recommendation,
            )

        return report
