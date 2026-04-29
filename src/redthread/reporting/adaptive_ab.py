"""Adaptive persona weighting A/B proof artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_METRICS = (
    "confirmed_findings",
    "risk_coverage_count",
    "strategy_coverage_count",
    "average_duration_seconds",
    "false_positive_proxy_count",
)


def compare_hero_proof_files(baseline_path: Path, adaptive_path: Path) -> dict[str, Any]:
    """Compare two hero proof bundles for adaptive weighting A/B review."""
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    adaptive = json.loads(adaptive_path.read_text(encoding="utf-8"))
    return compare_hero_proof_bundles(baseline, adaptive)


def compare_hero_proof_bundles(
    baseline: dict[str, Any],
    adaptive: dict[str, Any],
) -> dict[str, Any]:
    """Build a same-target/objective/budget comparison from two proof bundles."""
    baseline_metrics = dict(baseline.get("metrics", {}))
    adaptive_metrics = dict(adaptive.get("metrics", {}))
    gates = _gates(baseline, adaptive, baseline_metrics, adaptive_metrics)
    return {
        "schema_version": "redthread.adaptive_weighting_ab.v1",
        "comparison_scope": {
            "same_objective": gates["same_objective"],
            "same_target": gates["same_target"],
            "same_budget": gates["same_budget"],
            "valid_ab_scope": all(gates.values()),
        },
        "baseline_campaign_id": baseline.get("campaign_id", ""),
        "adaptive_campaign_id": adaptive.get("campaign_id", ""),
        "metric_deltas": _metric_deltas(baseline_metrics, adaptive_metrics),
        "decision_notes": _decision_notes(gates, baseline_metrics, adaptive_metrics),
        "limitations": [
            "A/B proof compares campaign artifacts only; it does not create findings.",
            "False positives use the non-confirmed detector-hint proxy until labeled review exists.",
        ],
    }


def write_adaptive_ab_report(
    report: dict[str, Any],
    output_path: Path,
) -> Path:
    """Persist an adaptive weighting A/B report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def _gates(
    baseline: dict[str, Any],
    adaptive: dict[str, Any],
    baseline_metrics: dict[str, Any],
    adaptive_metrics: dict[str, Any],
) -> dict[str, bool]:
    return {
        "same_objective": baseline.get("objective") == adaptive.get("objective"),
        "same_target": baseline.get("target_ids", []) == adaptive.get("target_ids", []),
        "same_budget": baseline_metrics.get("total_runs") == adaptive_metrics.get("total_runs"),
    }


def _metric_deltas(
    baseline_metrics: dict[str, Any],
    adaptive_metrics: dict[str, Any],
) -> dict[str, dict[str, float]]:
    deltas = {}
    for metric in _METRICS:
        base = float(baseline_metrics.get(metric, 0.0) or 0.0)
        adapted = float(adaptive_metrics.get(metric, 0.0) or 0.0)
        deltas[metric] = {"baseline": base, "adaptive": adapted, "delta": adapted - base}
    return deltas


def _decision_notes(
    gates: dict[str, bool],
    baseline_metrics: dict[str, Any],
    adaptive_metrics: dict[str, Any],
) -> list[str]:
    notes = []
    if not all(gates.values()):
        notes.append("Do not claim an A/B win until target, objective, and budget match.")
    if adaptive_metrics.get("confirmed_findings", 0) > baseline_metrics.get("confirmed_findings", 0):
        notes.append("Adaptive run found more confirmed findings under the compared budget.")
    if adaptive_metrics.get("false_positive_proxy_count", 0) > baseline_metrics.get("false_positive_proxy_count", 0):
        notes.append("Adaptive run increased the false-positive proxy; review before enabling by default.")
    return notes or ["No material adaptive weighting lift observed in this comparison."]


__all__ = [
    "compare_hero_proof_bundles",
    "compare_hero_proof_files",
    "write_adaptive_ab_report",
]
