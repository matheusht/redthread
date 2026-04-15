"""ASI sub-score functions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from redthread.telemetry.drift import DriftDetector
from redthread.telemetry.models import ArimaForecast

if TYPE_CHECKING:
    from redthread.telemetry.collector import TelemetryCollector

logger = logging.getLogger(__name__)


def score_response_consistency(collector: TelemetryCollector) -> tuple[float, str]:
    canary_ids = list({r.canary_id for r in collector.get_canary_records()})
    if not canary_ids:
        logger.debug("ASI | RC | no canary records → defaulting to 100")
        return 100.0, "no_canaries"
    scores: list[float] = []
    for cid in canary_ids:
        all_embeddings = [
            r.response_embedding
            for r in collector.get_canary_records(canary_id=cid)
            if r.response_embedding
        ]
        if len(all_embeddings) < 2:
            continue
        target_dim = len(all_embeddings[-1])
        embeddings = [e for e in all_embeddings if len(e) == target_dim]
        if len(embeddings) < 2:
            logger.warning(
                "ASI | RC | canary_id=%s | skipped %d records with mismatched dimensions (target_dim=%d)",
                cid,
                len(all_embeddings) - len(embeddings),
                target_dim,
            )
            continue
        mat = np.array(embeddings, dtype=np.float64)
        norms = np.where(np.linalg.norm(mat, axis=1, keepdims=True) == 0, 1.0, np.linalg.norm(mat, axis=1, keepdims=True))
        sim_matrix = np.dot(mat / norms, (mat / norms).T)
        scores.append(float(np.mean(sim_matrix[~np.eye(len(embeddings), dtype=bool)])))
    if not scores:
        return 100.0, "insufficient_canary_history"
    avg_sim = float(np.mean(scores))
    score = max(0.0, min(100.0, avg_sim * 100.0))
    logger.debug("ASI | RC | avg_cosine_sim=%.4f → score=%.1f", avg_sim, score)
    return score, "measured"


def score_semantic_drift(
    collector: TelemetryCollector,
    drift_detector: DriftDetector,
    window_size: int,
) -> tuple[float, str]:
    if drift_detector._baseline_embeddings is None:
        logger.debug("ASI | SD | no baseline fitted → defaulting to 100")
        return 100.0, "no_baseline"
    organic = collector.get_organic_records(window=window_size)
    all_embeddings = [r.response_embedding for r in organic if r.response_embedding]
    if not all_embeddings:
        return 100.0, "no_organic_embeddings"
    baseline_dim = drift_detector._baseline_embeddings.shape[1]
    embeddings = [e for e in all_embeddings if len(e) == baseline_dim]
    if not embeddings:
        logger.warning(
            "ASI | SD | skipped %d organic records with dimension != baseline_dim (%d)",
            len(all_embeddings),
            baseline_dim,
        )
        return 100.0, "embedding_dim_mismatch"
    drift_metrics = drift_detector.compute_drift(embeddings)
    avg_distance = float(np.mean([m["distance"] for m in drift_metrics]))
    if drift_detector._core_distances is None:
        return 100.0, "no_baseline"
    baseline_avg = float(np.mean(drift_detector._core_distances))
    threshold = 2.0 * baseline_avg if baseline_avg > 0 else 1.0
    score = max(0.0, min(100.0, (1.0 - avg_distance / threshold) * 100.0))
    logger.debug("ASI | SD | avg_k_dist=%.4f | baseline_avg=%.4f | score=%.1f", avg_distance, baseline_avg, score)
    return score, "measured"


def score_operational_health(forecasts: list[ArimaForecast]) -> tuple[float, str]:
    if not forecasts:
        logger.debug("ASI | OH | no forecasts → defaulting to 100")
        return 100.0, "insufficient_history"
    anomaly_count = sum(1 for forecast in forecasts if forecast.is_anomaly)
    score = max(0.0, min(100.0, (1.0 - anomaly_count / len(forecasts)) * 100.0))
    logger.debug("ASI | OH | anomalies=%d/%d → score=%.1f", anomaly_count, len(forecasts), score)
    return score, "measured"


def score_behavioral_stability(
    collector: TelemetryCollector,
    window_size: int,
) -> tuple[float, str]:
    token_series = collector.get_metric_series("output_tokens", window=window_size)
    if len(token_series) < 2:
        return 100.0, "insufficient_history"
    arr = np.array(token_series, dtype=np.float64)
    mean = float(np.mean(arr))
    cv = (float(np.std(arr)) / mean) if mean > 0 else 0.0
    score = max(0.0, min(100.0, (1.0 - min(cv, 1.0)) * 100.0))
    logger.debug("ASI | BS | cv=%.4f → score=%.1f", cv, score)
    return score, "measured"
