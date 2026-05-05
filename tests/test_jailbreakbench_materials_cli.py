"""Tests for JailbreakBench reviewed material vault imports."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from redthread.cli import main


def _source_file(tmp_path: Path, text: str) -> Path:
    source = tmp_path / "reviewed-jailbreakbench.txt"
    source.write_text(text, encoding="utf-8")
    return source


def test_import_jailbreakbench_redacted_material_uses_source_collection(tmp_path: Path) -> None:
    source = _source_file(tmp_path, "toy jailbreakbench redacted body")

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "import",
            "--source",
            "jailbreakbench",
            "--fixture-id",
            "jailbreakbench-0001",
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
    assert "Material class: redacted" in result.output
    assert "toy jailbreakbench redacted body" not in result.output
    assert (tmp_path / "jailbreakbench/redacted/jailbreakbench-0001.txt").exists()
    assert (tmp_path / "jailbreakbench/manifests/jailbreakbench-0001.json").exists()


def test_import_jailbreakbench_approved_seed_is_prompt_safe_json(tmp_path: Path) -> None:
    source = _source_file(tmp_path, "toy jailbreakbench approved seed")

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "import",
            "--source",
            "jailbreakbench",
            "--fixture-id",
            "jailbreakbench-0001",
            "--source-material",
            str(source),
            "--material-root",
            str(tmp_path),
            "--reviewed-by",
            "security-review-owner",
            "--reviewed-at",
            "2026-04-26T00:00:00Z",
            "--reviewer",
            "security-review-owner",
            "--reviewer",
            "benchmark-owner",
            "--material-class",
            "approved_replay_seed",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["manifest_ref"] == "jailbreakbench/manifests/jailbreakbench-0001.json"
    assert payload["material_ref"] == "jailbreakbench/reviewed/jailbreakbench-0001.txt"
    assert payload["manifest"]["source_path"].startswith("metadata-only/jailbreakbench")
    assert payload["manifest"]["reviewers"] == ["benchmark-owner", "security-review-owner"]
    assert "toy jailbreakbench approved seed" not in result.output


def test_jailbreakbench_ready_material_suggests_source_flag(tmp_path: Path) -> None:
    source = _source_file(tmp_path, "toy jailbreakbench command seed")
    import_result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "import",
            "--source",
            "jailbreakbench",
            "--fixture-id",
            "jailbreakbench-0001",
            "--source-material",
            str(source),
            "--material-root",
            str(tmp_path),
            "--reviewed-by",
            "security-review-owner",
            "--reviewed-at",
            "2026-04-26T00:00:00Z",
            "--reviewer",
            "security-review-owner",
            "--reviewer",
            "benchmark-owner",
            "--material-class",
            "approved_replay_seed",
            "--collection-id",
            "custom-jbb-set",
        ],
    )
    assert import_result.exit_code == 0

    list_result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "list",
            "--material-root",
            str(tmp_path),
            "--ready-only",
            "--replay-commands-only",
        ],
    )

    assert list_result.exit_code == 0
    assert "--source jailbreakbench" in list_result.output
    assert "--fixture-id jailbreakbench-0001" in list_result.output
    assert "--manifest-ref custom-jbb-set/manifests/jailbreakbench-0001.json" in list_result.output
    assert "toy jailbreakbench command seed" not in list_result.output
