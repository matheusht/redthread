"""Tests for reviewed benchmark material CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from redthread.cli import main


def _source_file(tmp_path: Path, text: str = "toy reviewed material") -> Path:
    source = tmp_path / "reviewed.txt"
    source.write_text(text, encoding="utf-8")
    return source


def test_import_material_cli_copies_redacted_material_without_printing_body(tmp_path: Path) -> None:
    source = _source_file(tmp_path, "toy redacted material body")

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "import",
            "--fixture-id",
            "spiritual-spell-0032",
            "--source-material",
            str(source),
            "--material-root",
            str(tmp_path),
            "--reviewed-by",
            "security-review-owner",
            "--reviewed-at",
            "2026-04-26T00:00:00Z",
        ],
    )

    assert result.exit_code == 0
    assert "REDTHREAD BENCHMARK MATERIAL IMPORT" in result.output
    assert "Material class: redacted" in result.output
    assert "toy redacted material body" not in result.output
    assert (tmp_path / "spiritual-spell/redacted/spiritual-spell-0032.txt").exists()
    assert (tmp_path / "spiritual-spell/manifests/spiritual-spell-0032.json").exists()


def test_import_material_cli_json_reports_manifest_ref(tmp_path: Path) -> None:
    source = _source_file(tmp_path)

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "import",
            "--fixture-id",
            "spiritual-spell-0032",
            "--source-material",
            str(source),
            "--material-root",
            str(tmp_path),
            "--reviewed-by",
            "security-review-owner",
            "--reviewed-at",
            "2026-04-26T00:00:00Z",
            "--material-class",
            "approved_replay_seed",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["manifest_ref"] == "spiritual-spell/manifests/spiritual-spell-0032.json"
    assert payload["manifest"]["material_class"] == "approved_replay_seed"
    assert payload["manifest"]["allowed_target_ids"] == ["local-dev"]


def test_import_material_cli_blocks_unknown_fixture(tmp_path: Path) -> None:
    source = _source_file(tmp_path)

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "import",
            "--fixture-id",
            "missing-fixture",
            "--source-material",
            str(source),
            "--material-root",
            str(tmp_path),
            "--reviewed-by",
            "security-review-owner",
            "--reviewed-at",
            "2026-04-26T00:00:00Z",
        ],
    )

    assert result.exit_code != 0
    assert "unknown jailbreak benchmark fixture id" in result.output


def test_import_material_cli_blocks_nonlocal_target_without_override(tmp_path: Path) -> None:
    source = _source_file(tmp_path)

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "import",
            "--fixture-id",
            "spiritual-spell-0032",
            "--source-material",
            str(source),
            "--material-root",
            str(tmp_path),
            "--reviewed-by",
            "security-review-owner",
            "--reviewed-at",
            "2026-04-26T00:00:00Z",
            "--material-class",
            "approved_replay_seed",
            "--allowed-target",
            "prod-model",
        ],
    )

    assert result.exit_code != 0
    assert "non-local target approval requires explicit override" in result.output
