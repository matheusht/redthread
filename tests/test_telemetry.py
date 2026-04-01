"""Tests for Phase 4.5 Telemetry (Embeddings & Drift)."""

from __future__ import annotations

import httpx
import numpy as np
import pytest

from redthread.config.settings import RedThreadSettings, TargetBackend
from redthread.telemetry.drift import DriftDetector
from redthread.telemetry.embeddings import EmbeddingClient


@pytest.fixture
def dry_run_settings() -> RedThreadSettings:
    return RedThreadSettings(
        target_backend=TargetBackend.OPENAI,
        target_model="gpt-4o",
        attacker_backend=TargetBackend.OLLAMA,
        attacker_model="llama3.2:3b",
        judge_backend=TargetBackend.OPENAI,
        judge_model="gpt-4o",
        openai_api_key="sk-test",
        dry_run=True,
    )


@pytest.mark.asyncio
async def test_embedding_client_dry_run(dry_run_settings: RedThreadSettings) -> None:
    """EmbeddingClient should return deterministic random vectors in dry_run."""
    client = EmbeddingClient(dry_run_settings)

    emb1 = await client.embed("Test sentence one.")
    emb2 = await client.embed("Test sentence two.")
    emb1_again = await client.embed("Test sentence one.")

    assert len(emb1) == 1536
    assert len(emb2) == 1536
    assert emb1 == emb1_again  # Deterministic hash baseline
    assert emb1 != emb2


def test_drift_detector_baseline_fitting() -> None:
    """DriftDetector should correctly fit baseline and prune k if data is small."""
    detector = DriftDetector(k_neighbors=5, distance_metric="cosine")

    # Pass 3 samples, k_neighbors should drop to 2
    embeddings = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]

    detector.fit_baseline(embeddings)

    assert detector.k_neighbors == 2
    assert detector._core_distances is not None
    assert len(detector._core_distances) == 3


def test_drift_detector_computes_distance() -> None:
    """DriftDetector should compute K Core-Distance and flag anomalies."""
    detector = DriftDetector(k_neighbors=1, distance_metric="euclidean")
    
    # Baseline: points near origin
    baseline = [
        [0.1, 0.1],
        [0.2, 0.1],
        [0.1, 0.2],
    ]
    detector.fit_baseline(baseline)

    # Test: One near baseline, one far anomaly
    test_data = [
        [0.15, 0.15], # Dist approx 0.07 -> not anomaly
        [5.0, 5.0],   # Dist approx 6.9 -> anomaly
    ]

    results = detector.compute_drift(test_data)

    assert len(results) == 2
    assert results[0]["is_anomaly"] is False
    assert results[0]["distance"] < 1.0
    
    assert results[1]["is_anomaly"] is True
    assert results[1]["distance"] > 3.0
