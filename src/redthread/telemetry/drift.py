"""Data Drift and K Core-Distance Telemetry (Phase 4.5).

Analyzes the divergence of target responses from a baseline distribution using
embeddings. This detects when guardrail injection inherently shifts the overall
target alignment or tone (over-refusals, performance dropping).
"""

from __future__ import annotations

import logging
from typing import TypedDict

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


class DriftMetric(TypedDict):
    distance: float
    is_anomaly: bool


class DriftDetector:
    """Computes distribution shift via K Core-Distance on textual embeddings."""

    def __init__(self, k_neighbors: int = 5, distance_metric: str = "cosine") -> None:
        self.k_neighbors = k_neighbors
        self.distance_metric = distance_metric
        
        self._baseline_embeddings: NDArray[np.float64] | None = None
        
        self._core_distances: NDArray[np.float64] | None = None

    def _cosine_distance(self, a: NDArray[np.float64], b: NDArray[np.float64]) -> NDArray[np.float64]:
        """Compute pairwise cosine distance matrix between A and B."""
        a_norms = np.linalg.norm(a, axis=1, keepdims=True)
        b_norms = np.linalg.norm(b, axis=1, keepdims=True)
        a_denominator = np.where(a_norms == 0.0, 1.0, a_norms)
        b_denominator = np.where(b_norms == 0.0, 1.0, b_norms)
        a_norm = a / a_denominator
        b_norm = b / b_denominator
        sim = np.dot(a_norm, b_norm.T)
        return 1.0 - sim

    def fit_baseline(self, embeddings: list[list[float]]) -> None:
        """Cache baseline embeddings and compute core distances for density estimation."""
        if not embeddings:
            raise ValueError("Empty embeddings list.")

        self._baseline_embeddings = np.array(embeddings, dtype=np.float64)
        N = self._baseline_embeddings.shape[0]

        if self.k_neighbors > N:
            logger.warning("Baseline size (%d) < k_neighbors (%d). Reducing k.", N, self.k_neighbors)
            self.k_neighbors = max(1, N - 1)

        if self.distance_metric == "cosine":
            dist_matrix = self._cosine_distance(self._baseline_embeddings, self._baseline_embeddings)
        else:
            diff = self._baseline_embeddings[:, np.newaxis, :] - self._baseline_embeddings[np.newaxis, :, :]
            dist_matrix = np.sqrt(np.sum(diff**2, axis=-1))

        sorted_dist = np.sort(dist_matrix, axis=1)
        self._core_distances = sorted_dist[:, self.k_neighbors]

        logger.info(
            "📈 DriftDetector | Baseline fitted | N=%d | avg_k_dist=%.4f",
            N,
            float(np.mean(self._core_distances))
        )

    def compute_drift(self, test_embeddings: list[list[float]]) -> list[DriftMetric]:
        """Compute K Core-Distance for each test sample against the baseline distribution."""
        if self._baseline_embeddings is None or self._core_distances is None:
            raise RuntimeError("DriftDetector is not fitted. Call fit_baseline first.")

        test_mat = np.array(test_embeddings, dtype=np.float64)
        
        if self.distance_metric == "cosine":
            dist_matrix = self._cosine_distance(test_mat, self._baseline_embeddings)
        else:
            diff = test_mat[:, np.newaxis, :] - self._baseline_embeddings[np.newaxis, :, :]
            dist_matrix = np.sqrt(np.sum(diff**2, axis=-1))

        results: list[DriftMetric] = []
        
        for i in range(test_mat.shape[0]):
            dists_to_baseline = dist_matrix[i, :]
            sorted_dists = np.sort(dists_to_baseline)
            
            k_dist = sorted_dists[self.k_neighbors]
            
            avg_baseline = float(np.mean(self._core_distances))
            is_anomaly = float(k_dist) > (2.0 * avg_baseline)

            results.append(DriftMetric(
                distance=float(k_dist),
                is_anomaly=is_anomaly
            ))

        return results
