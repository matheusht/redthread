"""Tests for ready-only benchmark material inventory filtering."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from redthread.benchmarks.material_inventory import list_benchmark_material_manifests
from redthread.benchmarks.material_review import import_reviewed_material
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures
from redthread.cli import main


def _import_material(tmp_path: Path, *, collection_id: str, fixture_id: str, text: str) -> None:
    fixture = next(item for item in load_spiritual_spell_fixtures() if item.id == fixture_id)
    source = tmp_path / f"{collection_id}.txt"
    source.write_text(text, encoding="utf-8")
    import_reviewed_material(
        fixture,
        source_material_path=source,
        material_root=tmp_path,
        reviewed_by="security-review-owner",
        reviewed_at="2026-04-26T00:00:00Z",
        reviewer_ids=["security-review-owner", "benchmark-owner"],
        material_class="approved_replay_seed",
        collection_id=collection_id,
    )


def test_material_inventory_filters_ready_only(tmp_path: Path) -> None:
    _import_material(
        tmp_path,
        collection_id="ready-set",
        fixture_id="spiritual-spell-0032",
        text="ready only visible body",
    )
    _import_material(
        tmp_path,
        collection_id="blocked-set",
        fixture_id="spiritual-spell-0033",
        text="blocked ready only body",
    )
    blocked_path = tmp_path / "blocked-set" / "reviewed" / "spiritual-spell-0033.txt"
    blocked_path.write_text("tampered ready only body", encoding="utf-8")

    inventory = list_benchmark_material_manifests(material_root=tmp_path, verify_hashes=True, ready_only=True)

    assert inventory.ready_only is True
    assert inventory.manifest_count == 1
    assert inventory.engine_decision == "ready_for_replay"
    assert inventory.manifests[0].collection_id == "ready-set"
    assert inventory.manifests[0].hash_status == "verified"
    assert "ready only visible body" not in inventory.model_dump_json()
    assert "tampered ready only body" not in inventory.model_dump_json()


def test_material_inventory_cli_ready_only_is_prompt_safe(tmp_path: Path) -> None:
    _import_material(
        tmp_path,
        collection_id="ready-cli-set",
        fixture_id="spiritual-spell-0032",
        text="ready only cli body",
    )

    result = CliRunner().invoke(
        main,
        ["eval", "jailbreak-material", "list", "--material-root", str(tmp_path), "--ready-only", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ready_only"] is True
    assert payload["manifest_count"] == 1
    assert payload["manifests"][0]["collection_id"] == "ready-cli-set"
    assert "ready only cli body" not in result.output


def test_material_inventory_cli_prints_replay_commands_only(tmp_path: Path) -> None:
    _import_material(
        tmp_path,
        collection_id="commands-only-set",
        fixture_id="spiritual-spell-0032",
        text="commands only cli body",
    )

    result = CliRunner().invoke(
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

    assert result.exit_code == 0
    assert result.output.startswith("redthread eval jailbreak-corpus --replay")
    assert "--fixture-id spiritual-spell-0032" in result.output
    assert "--material-root" in result.output
    assert "REDTHREAD BENCHMARK MATERIAL INVENTORY" not in result.output
    assert "commands only cli body" not in result.output


def test_replay_commands_only_does_not_emit_blocked_material(tmp_path: Path) -> None:
    _import_material(
        tmp_path,
        collection_id="blocked-commands-set",
        fixture_id="spiritual-spell-0032",
        text="blocked commands only body",
    )
    material_path = tmp_path / "blocked-commands-set" / "reviewed" / "spiritual-spell-0032.txt"
    material_path.write_text("tampered blocked commands body", encoding="utf-8")

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "list",
            "--material-root",
            str(tmp_path),
            "--replay-commands-only",
        ],
    )

    assert result.exit_code == 0
    assert result.output == ""
    assert "blocked commands only body" not in result.output
    assert "tampered blocked commands body" not in result.output
