"""Tests for prompt-safe benchmark material verification CLI."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from redthread.cli import main


def _source_file(tmp_path: Path, text: str = "toy reviewed verify material") -> Path:
    source = tmp_path / "reviewed.txt"
    source.write_text(text, encoding="utf-8")
    return source


def _import_material(tmp_path: Path, text: str = "toy reviewed verify material") -> str:
    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "import",
            "--fixture-id",
            "spiritual-spell-0032",
            "--source-material",
            str(_source_file(tmp_path, text)),
            "--material-root",
            str(tmp_path),
            "--reviewed-by",
            "security-review-owner",
            "--reviewed-at",
            "2026-04-26T00:00:00Z",
            "--material-class",
            "approved_replay_seed",
            "--reviewer",
            "security-review-owner",
            "--reviewer",
            "benchmark-owner",
            "--json",
        ],
    )
    assert result.exit_code == 0
    return str(json.loads(result.output)["manifest_ref"])


def test_verify_material_cli_confirms_hash_without_printing_body(tmp_path: Path) -> None:
    manifest_ref = _import_material(tmp_path, "toy verify prompt body")

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "verify",
            "--manifest-ref",
            manifest_ref,
            "--material-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "REDTHREAD BENCHMARK MATERIAL VERIFY" in result.output
    assert "Hash verified: True" in result.output
    assert "Raw prompt body: not printed" in result.output
    assert "toy verify prompt body" not in result.output


def test_verify_material_cli_json_is_prompt_safe(tmp_path: Path) -> None:
    manifest_ref = _import_material(tmp_path, "toy verify json prompt body")

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "verify",
            "--manifest-ref",
            manifest_ref,
            "--material-root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["fixture_id"] == "spiritual-spell-0032"
    assert payload["hash_verified"] is True
    assert payload["reviewers"] == ["benchmark-owner", "security-review-owner"]
    assert "toy verify json prompt body" not in result.output


def test_verify_material_cli_blocks_hash_mismatch(tmp_path: Path) -> None:
    manifest_ref = _import_material(tmp_path, "toy verified before tamper")
    material_path = tmp_path / "spiritual-spell" / "reviewed" / "spiritual-spell-0032.txt"
    material_path.write_text("tampered body", encoding="utf-8")

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "verify",
            "--manifest-ref",
            manifest_ref,
            "--material-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code != 0
    assert "hash does not match" in result.output
    assert "tampered body" not in result.output
