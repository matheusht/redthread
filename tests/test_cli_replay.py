from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from redthread.cli import main


def _write_bundle(path: Path, *, decision: str, canary_contained: bool = True) -> None:
    path.write_text(
        json.dumps(
            {
                "bundle_id": "replay-cli-test",
                "bridge_workflow_context": {"workflow_count": 1},
                "traces": [
                    {
                        "trace_id": "trace-1",
                        "threat": "confused_deputy",
                        "scenario_result": {"executed": True},
                        "authorization_decision": {"decision": decision},
                        "expected_authorization": "deny",
                        "canary_report": {"contained": canary_contained},
                        "budget_decision": {"stop_triggered": False},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_replay_run_renders_passing_bundle(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle.json"
    _write_bundle(bundle, decision="deny")

    result = CliRunner().invoke(main, ["replay", "run", str(bundle)])

    assert result.exit_code == 0, result.output
    assert "replay-cli-test" in result.output
    assert "trace-1" in result.output
    assert "PASS" in result.output
    assert "Authorization" in result.output
    assert "Canary" in result.output
    assert "Budget" in result.output


def test_replay_run_returns_nonzero_for_failed_bundle(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle.json"
    _write_bundle(bundle, decision="allow")

    result = CliRunner().invoke(main, ["replay", "run", str(bundle)])

    assert result.exit_code != 0
    assert "FAIL" in result.output
    assert "trace-1:authorization:allow" in result.output


def test_replay_run_reports_canary_mismatch(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle.json"
    _write_bundle(bundle, decision="deny", canary_contained=False)
    payload = json.loads(bundle.read_text(encoding="utf-8"))
    payload["traces"][0]["expect_canary_contained"] = True
    bundle.write_text(json.dumps(payload), encoding="utf-8")

    result = CliRunner().invoke(main, ["replay", "run", str(bundle)])

    assert result.exit_code != 0
    assert "trace-1:canary:False" in result.output


def test_replay_run_rejects_invalid_json(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle.json"
    bundle.write_text("not-json", encoding="utf-8")

    result = CliRunner().invoke(main, ["replay", "run", str(bundle)])

    assert result.exit_code != 0
    assert "Invalid replay bundle" in result.output


def test_replay_run_rejects_schema_invalid_json(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle.json"
    bundle.write_text(json.dumps({"bundle_id": "missing-threat", "traces": [{}]}), encoding="utf-8")

    result = CliRunner().invoke(main, ["replay", "run", str(bundle)])

    assert result.exit_code != 0
    assert "Invalid replay bundle" in result.output
