from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from rich.console import Console

from redthread.cli import main
from redthread.dashboard import export_campaign_history, filter_campaign_history, render_dashboard
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


def test_filter_and_export_campaign_history() -> None:
    campaigns = [
        {
            "id": "c1",
            "algorithm": "PAIR",
            "attack_success_rate": 0.5,
            "started_at": "2026-09-01T10:00:00",
        },
        {
            "id": "c2",
            "algorithm": "TAP",
            "attack_success_rate": 0.0,
            "started_at": "2026-09-02T10:00:00",
        },
    ]

    by_algo = filter_campaign_history(campaigns, algorithm="pair")
    assert len(by_algo) == 1 and by_algo[0]["id"] == "c1"

    by_outcome_jb = filter_campaign_history(campaigns, outcome="jailbreak")
    assert len(by_outcome_jb) == 1 and by_outcome_jb[0]["id"] == "c1"

    by_outcome_bn = filter_campaign_history(campaigns, outcome="benign")
    assert len(by_outcome_bn) == 1 and by_outcome_bn[0]["id"] == "c2"

    by_since = filter_campaign_history(campaigns, since="2026-09-02")
    assert len(by_since) == 1 and by_since[0]["id"] == "c2"

    json_out = export_campaign_history(campaigns, "json")
    assert json.loads(json_out) == campaigns

    csv_out = export_campaign_history(campaigns, "csv")
    assert "id,started_at" in csv_out
    assert "c1,2026-09-01T10:00:00" in csv_out


def test_cli_dashboard_export_flags(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    _write_campaign_log(
        log_dir / "camp-test.jsonl",
        {
            "type": "campaign_result",
            "id": "c-test-1",
            "started_at": "2026-09-18T10:00:00",
            "target_model": "test-model",
            "algorithm": "MCTS",
            "attack_success_rate": 0.0,
            "average_score": 1.0,
            "num_runs": 1,
        },
    )

    runner = CliRunner()
    res_json = runner.invoke(main, ["dashboard", "--log-dir", str(log_dir), "--export", "json"])
    assert res_json.exit_code == 0
    assert "c-test-1" in res_json.output

    res_csv = runner.invoke(main, ["dashboard", "--log-dir", str(log_dir), "--export", "csv"])
    assert res_csv.exit_code == 0
    assert "c-test-1" in res_csv.output
