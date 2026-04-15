"""Truth-boundary tests for telemetry reporting."""

from __future__ import annotations

from pathlib import Path

import pytest

from redthread.config.settings import RedThreadSettings, TargetBackend
from redthread.telemetry.asi import AgentStabilityIndex
from redthread.telemetry.collector import TelemetryCollector
from redthread.telemetry.drift import DriftDetector
from redthread.telemetry.models import TelemetryRecord


@pytest.fixture
def settings(tmp_path: Path) -> RedThreadSettings:
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
        log_dir=tmp_path / "logs",
        memory_dir=tmp_path / "memory",
    )


def _record(
    *,
    idx: int,
    canary: bool,
    embedding: list[float],
    canary_id: str = "",
) -> TelemetryRecord:
    return TelemetryRecord(
        target_model="gpt-4o",
        prompt_hash=f"hash-{idx}",
        latency_ms=100.0,
        input_tokens=10,
        output_tokens=20,
        response_text="hello world",
        response_embedding=embedding,
        is_canary=canary,
        canary_id=canary_id,
    )


def test_missing_baseline_is_reported_as_limited_evidence(settings: RedThreadSettings) -> None:
    collector = TelemetryCollector(settings)
    collector.storage.insert(_record(idx=1, canary=False, embedding=[1.0, 0.0, 0.0]))
    collector.storage.insert(_record(idx=2, canary=False, embedding=[1.0, 0.0, 0.0]))

    report = AgentStabilityIndex(settings).compute(collector)

    assert report.semantic_drift == pytest.approx(100.0)
    assert report.metadata["semantic_drift_mode"] == "no_baseline"
    warnings = report.metadata["evidence_warnings"]
    assert any("no benign baseline" in warning for warning in warnings)
    assert "evidence is limited" in report.recommendation.lower()


def test_canary_only_monitoring_is_marked_as_signal_not_proof(settings: RedThreadSettings) -> None:
    collector = TelemetryCollector(settings)
    collector.storage.insert(
        _record(idx=1, canary=True, embedding=[1.0, 0.0, 0.0], canary_id="canary-001")
    )
    collector.storage.insert(
        _record(idx=2, canary=True, embedding=[1.0, 0.0, 0.0], canary_id="canary-001")
    )

    drift_detector = DriftDetector(k_neighbors=1, distance_metric="cosine")
    drift_detector.fit_baseline([[1.0, 0.0, 0.0], [0.9, 0.1, 0.0]])

    report = AgentStabilityIndex(settings, drift_detector=drift_detector).compute(collector)

    assert report.metadata["organic_records"] == 0
    assert report.metadata["canary_records"] == 2
    assert report.metadata["semantic_drift_mode"] == "no_organic_embeddings"
    warnings = report.metadata["evidence_warnings"]
    assert any("canary-only" in warning.lower() for warning in warnings)
    assert any("no organic response embeddings" in warning.lower() for warning in warnings)
    assert "operator signal" in report.recommendation.lower() or "evidence is limited" in report.recommendation.lower()


def test_measured_inputs_do_not_emit_evidence_warnings(settings: RedThreadSettings) -> None:
    collector = TelemetryCollector(settings)
    for idx in range(25):
        collector.storage.insert(
            _record(idx=idx, canary=False, embedding=[1.0, 0.0, 0.0])
        )
    for idx in range(2):
        collector.storage.insert(
            _record(idx=100 + idx, canary=True, embedding=[1.0, 0.0, 0.0], canary_id="canary-001")
        )

    drift_detector = DriftDetector(k_neighbors=1, distance_metric="cosine")
    drift_detector.fit_baseline([[1.0, 0.0, 0.0], [0.9, 0.1, 0.0]])

    report = AgentStabilityIndex(settings, drift_detector=drift_detector).compute(collector)

    assert report.metadata["response_consistency_mode"] == "measured"
    assert report.metadata["semantic_drift_mode"] == "measured"
    assert report.metadata["evidence_warnings"] == []
