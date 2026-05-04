"""Tests for benchmark evaluation CLI dry-runs."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from redthread.cli import main


def test_jailbreak_corpus_cli_dry_run_prints_safe_summary() -> None:
    result = CliRunner().invoke(
        main,
        ["eval", "jailbreak-corpus", "--fixture-id", "spiritual-spell-0032"],
    )

    assert result.exit_code == 0
    assert "REDTHREAD JAILBREAK BENCHMARK DRY-RUN" in result.output
    assert "Selected fixtures: 1 / 210" in result.output
    assert "Evidence mode: metadata_only" in result.output
    assert "Raw prompt bodies: not loaded" in result.output
    assert "Target calls: not executed" in result.output
    assert "Scorecard: not scored (dry_run_no_execution)" in result.output
    assert "spiritual-spell-0032" in result.output


def test_jailbreak_corpus_cli_json_output_is_machine_readable() -> None:
    result = CliRunner().invoke(
        main,
        ["eval", "jailbreak-corpus", "--fixture-id", "spiritual-spell-0032", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == "redthread.jailbreak_benchmark_dry_run.v1"
    assert payload["selected_fixture_ids"] == ["spiritual-spell-0032"]
    assert payload["blocked_fixture_ids"] == ["spiritual-spell-0032"]
    assert payload["evidence_mode"] == "metadata_only"
    assert payload["not_scored_reason"] == "dry_run_no_execution"
    assert payload["scorecard"]["not_scored_reason"] == "dry_run_no_execution"
    assert payload["raw_prompt_policy"] == "raw prompt bodies are not loaded during dry-run"


def test_jailbreak_corpus_cli_can_show_safe_hints() -> None:
    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-corpus",
            "--fixture-id",
            "spiritual-spell-0032",
            "--show-hints",
        ],
    )

    assert result.exit_code == 0
    assert "Safe planning hints" in result.output
    assert "relational_persona_pressure" in result.output


def test_jailbreak_corpus_cli_writes_report_artifact(tmp_path: Path) -> None:
    output_path = tmp_path / "dry-run-report.json"

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-corpus",
            "--fixture-id",
            "spiritual-spell-0032",
            "--report-out",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert "Report written:" in result.output
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["selected_fixture_ids"] == ["spiritual-spell-0032"]


def test_jailbreak_corpus_cli_blocks_live_target_by_default() -> None:
    result = CliRunner().invoke(
        main,
        ["eval", "jailbreak-corpus", "--target", "prod-model"],
    )

    assert result.exit_code != 0
    assert "local-dev" in result.output
