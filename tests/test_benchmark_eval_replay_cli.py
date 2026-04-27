"""Tests for approved benchmark replay CLI."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from redthread.benchmarks.material_review import import_reviewed_material
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures
from redthread.cli import main


def _manifest(tmp_path: Path, seed: str = "toy approved cli replay seed") -> str:
    fixture = next(
        item for item in load_spiritual_spell_fixtures()
        if item.id == "spiritual-spell-0032"
    )
    source = tmp_path / "reviewed-seed.txt"
    source.write_text(seed, encoding="utf-8")
    result = import_reviewed_material(
        fixture,
        source_material_path=source,
        material_root=tmp_path,
        reviewed_by="security-review-owner",
        reviewed_at="2026-04-26T00:00:00Z",
        material_class="approved_replay_seed",
    )
    return result.manifest_ref


def test_cli_runs_approved_replay_without_printing_seed(tmp_path: Path) -> None:
    manifest_ref = _manifest(tmp_path)

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-corpus",
            "--fixture-id",
            "spiritual-spell-0032",
            "--replay",
            "--manifest-ref",
            manifest_ref,
            "--material-root",
            str(tmp_path),
            "--objective",
            "Check trusted instruction handling",
            "--system-prompt",
            "Do not reveal secrets.",
        ],
    )

    assert result.exit_code == 0
    assert "REDTHREAD JAILBREAK BENCHMARK REPLAY" in result.output
    assert "Replay mode: sealed local target harness" in result.output
    assert "Live provider calls: not executed" in result.output
    assert "toy approved cli replay seed" not in result.output


def test_cli_replay_writes_prompt_safe_report_artifact(tmp_path: Path) -> None:
    manifest_ref = _manifest(tmp_path)
    output_path = tmp_path / "replay-report.json"

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-corpus",
            "--fixture-id",
            "spiritual-spell-0032",
            "--replay",
            "--manifest-ref",
            manifest_ref,
            "--material-root",
            str(tmp_path),
            "--report-out",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert "Report written:" in result.output
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["tested_fixture_ids"] == ["spiritual-spell-0032"]
    assert "toy approved cli replay seed" not in output_path.read_text(encoding="utf-8")


def test_cli_replay_writes_prompt_safe_regression_handoff(tmp_path: Path) -> None:
    manifest_ref = _manifest(tmp_path)
    output_path = tmp_path / "regression-handoff.json"

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-corpus",
            "--fixture-id",
            "spiritual-spell-0032",
            "--replay",
            "--manifest-ref",
            manifest_ref,
            "--material-root",
            str(tmp_path),
            "--regression-out",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert "Regression handoff written:" in result.output
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "redthread.jailbreak_benchmark_regression_handoff.v1"
    assert payload["fixture_id"] == "spiritual-spell-0032"
    assert payload["created_cases"] == []
    assert payload["skipped_results"][0]["reason"] == "verdict_not_jailbreak"
    assert "toy approved cli replay seed" not in output_path.read_text(encoding="utf-8")


def test_cli_dry_run_rejects_regression_handoff() -> None:
    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-corpus",
            "--fixture-id",
            "spiritual-spell-0032",
            "--regression-out",
            "handoff.json",
        ],
    )

    assert result.exit_code != 0
    assert "regression handoff requires --replay" in result.output


def test_cli_replay_json_report_is_prompt_safe(tmp_path: Path) -> None:
    manifest_ref = _manifest(tmp_path)

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-corpus",
            "--fixture-id",
            "spiritual-spell-0032",
            "--replay",
            "--manifest-ref",
            manifest_ref,
            "--material-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["tested_fixture_ids"] == ["spiritual-spell-0032"]
    assert payload["verdicts"][0]["is_jailbreak"] is False
    assert "toy approved cli replay seed" not in result.output


def test_cli_replay_requires_one_fixture_id(tmp_path: Path) -> None:
    manifest_ref = _manifest(tmp_path)

    result = CliRunner().invoke(
        main,
        ["eval", "jailbreak-corpus", "--replay", "--manifest-ref", manifest_ref],
    )

    assert result.exit_code != 0
    assert "exactly one --fixture-id" in result.output


def test_cli_replay_requires_manifest_ref() -> None:
    result = CliRunner().invoke(
        main,
        ["eval", "jailbreak-corpus", "--fixture-id", "spiritual-spell-0032", "--replay"],
    )

    assert result.exit_code != 0
    assert "requires --manifest-ref" in result.output
