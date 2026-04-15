from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console

from redthread.dashboard import render_dashboard
from redthread.dashboard_history import load_campaign_history


def _write_campaign_log(path: Path, summary: dict, asi_report: dict | None = None) -> None:
    entries = [summary]
    if asi_report is not None:
        entries.append(asi_report)
    path.write_text("\n".join(json.dumps(entry) for entry in entries) + "\n", encoding="utf-8")


def test_load_campaign_history_parses_runtime_truth_fields(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    _write_campaign_log(
        log_dir / "campaign-1.jsonl",
        {
            "type": "campaign_result",
            "id": "campaign-1234567890",
            "started_at": "2026-04-15T12:00:00+00:00",
            "target_model": "llama3.2:3b",
            "algorithm": "tap",
            "runtime_mode": "sealed_dry_run",
            "telemetry_mode": "skipped_in_dry_run",
            "degraded_runtime": True,
            "error_count": 2,
            "runtime_summary": {
                "attack_worker_failures": 1,
                "judge_worker_failures": 1,
                "defense_worker_failures": 0,
            },
            "num_runs": 2,
            "attack_success_rate": 0.0,
            "average_score": 1.5,
        },
        {
            "type": "asi_report",
            "asi_score": 81.0,
            "health_tier": "healthy",
            "is_alert": False,
        },
    )

    history = load_campaign_history(log_dir)

    assert len(history) == 1
    record = history[0]
    assert record["runtime_mode"] == "sealed_dry_run"
    assert record["telemetry_mode"] == "skipped_in_dry_run"
    assert record["degraded_runtime"] is True
    assert record["error_count"] == 2
    assert record["attack_worker_failures"] == 1
    assert record["judge_worker_failures"] == 1
    assert record["asi_score"] == 81.0


def test_render_dashboard_surfaces_runtime_truth() -> None:
    console = Console(record=True, width=160)
    history = [
        {
            "id": "campaign-1234",
            "started_at": "2026-04-15T12:00:00+00:00",
            "target_model": "llama3.2:3b",
            "algorithm": "TAP",
            "runtime_mode": "sealed_dry_run",
            "telemetry_mode": "skipped_in_dry_run",
            "degraded_runtime": True,
            "error_count": 2,
            "attack_worker_failures": 1,
            "judge_worker_failures": 1,
            "defense_worker_failures": 0,
            "attack_success_rate": 0.0,
            "average_score": 1.5,
            "num_runs": 2,
            "asi_score": 81.0,
            "health_tier": "healthy",
            "is_alert": False,
        }
    ]

    render_dashboard(history, console)
    output = console.export_text()

    assert "sealed_dry_run/skipped_in_dry_run" in output
    assert "degraded 2e A1/J1/D0" in output
    assert "campaign-1234" in output
