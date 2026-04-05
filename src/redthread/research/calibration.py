"""Baseline-derived control calibration for autoresearch supervisor gates."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from redthread.research.models import BaselineCalibration, ResearchConfig


def load_calibration(
    results_path: Path,
    registry_path: Path,
    config: ResearchConfig,
) -> BaselineCalibration | None:
    """Load or derive baseline calibration from the research ledger."""
    if registry_path.exists():
        return BaselineCalibration.model_validate(json.loads(registry_path.read_text(encoding="utf-8")))

    rows = _baseline_rows(results_path)
    if not rows:
        return None

    asr_values = [float(row["average_asr"]) for row in rows]
    score_values = [float(row["average_score"]) for row in rows]
    calibration = BaselineCalibration(
        sample_count=len(rows),
        asr_mean=_mean(asr_values),
        asr_stdev=_stdev(asr_values),
        asr_p95=_percentile(asr_values, 0.95),
        asr_max=max(asr_values, default=0.0),
        score_mean=_mean(score_values),
        score_stdev=_stdev(score_values),
        score_p95=_percentile(score_values, 0.95),
        score_max=max(score_values, default=0.0),
    )
    calibration.control_max_average_asr = max(
        config.control_max_average_asr,
        calibration.asr_max,
        calibration.asr_p95,
        calibration.asr_mean + (2.0 * calibration.asr_stdev),
    )
    calibration.control_max_average_score = max(
        config.control_max_average_score,
        calibration.score_max,
        calibration.score_p95,
        calibration.score_mean + (2.0 * calibration.score_stdev),
    )
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(calibration.model_dump_json(indent=2), encoding="utf-8")
    return calibration


def _baseline_rows(results_path: Path) -> list[dict[str, str]]:
    if not results_path.exists():
        return []
    with results_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [row for row in reader if row.get("mode") == "baseline"]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(variance)


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    index = (len(ordered) - 1) * q
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return ordered[low]
    fraction = index - low
    return ordered[low] + ((ordered[high] - ordered[low]) * fraction)
