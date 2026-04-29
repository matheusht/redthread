from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from redthread.cli import main
from redthread.reporting.adaptive_ab import compare_hero_proof_bundles, write_adaptive_ab_report


def _proof(campaign_id: str, findings: int, false_positive_proxy: int = 0) -> dict[str, object]:
    return {
        "schema_version": "redthread.hero_proof.v1",
        "campaign_id": campaign_id,
        "objective": "test trusted instruction handling",
        "target_ids": ["support-agent-dev"],
        "metrics": {
            "total_runs": 3,
            "confirmed_findings": findings,
            "risk_coverage_count": 2,
            "strategy_coverage_count": 2,
            "average_duration_seconds": 1.0,
            "false_positive_proxy_count": false_positive_proxy,
        },
    }


def test_compare_hero_proof_bundles_checks_same_scope_and_metric_deltas() -> None:
    report = compare_hero_proof_bundles(_proof("base", 1), _proof("adaptive", 2))

    assert report["schema_version"] == "redthread.adaptive_weighting_ab.v1"
    assert report["comparison_scope"]["valid_ab_scope"] is True
    assert report["metric_deltas"]["confirmed_findings"]["delta"] == 1.0
    assert "more confirmed findings" in " ".join(report["decision_notes"])


def test_compare_hero_proof_bundles_rejects_mismatched_budget() -> None:
    baseline = _proof("base", 1)
    adaptive = _proof("adaptive", 2)
    adaptive["metrics"]["total_runs"] = 4  # type: ignore[index]

    report = compare_hero_proof_bundles(baseline, adaptive)

    assert report["comparison_scope"]["valid_ab_scope"] is False
    assert "Do not claim an A/B win" in " ".join(report["decision_notes"])


def test_write_adaptive_ab_report_persists_json(tmp_path: Path) -> None:
    output = tmp_path / "ab.json"
    report = compare_hero_proof_bundles(_proof("base", 1), _proof("adaptive", 1))

    write_adaptive_ab_report(report, output)

    assert json.loads(output.read_text())["schema_version"] == "redthread.adaptive_weighting_ab.v1"


def test_compare_weighting_cli_writes_report(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline-hero-proof.json"
    adaptive = tmp_path / "adaptive-hero-proof.json"
    output = tmp_path / "ab.json"
    baseline.write_text(json.dumps(_proof("base", 1)), encoding="utf-8")
    adaptive.write_text(json.dumps(_proof("adaptive", 2)), encoding="utf-8")

    result = CliRunner().invoke(
        main,
        [
            "evidence",
            "compare-weighting",
            "--baseline-hero-proof",
            str(baseline),
            "--adaptive-hero-proof",
            str(adaptive),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0
    assert "valid adaptive weighting A/B proof" in result.output
    assert json.loads(output.read_text())["comparison_scope"]["valid_ab_scope"] is True
