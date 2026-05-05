"""Tests for prompt-safe invalid hash inventory filtering."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from redthread.benchmarks.material_inventory import list_benchmark_material_manifests
from redthread.benchmarks.material_review import import_reviewed_material
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures
from redthread.cli import main


def _manifest(tmp_path: Path, collection_id: str, text: str) -> None:
    fixture = next(
        item for item in load_spiritual_spell_fixtures()
        if item.id == "spiritual-spell-0032"
    )
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


def test_inventory_can_return_only_invalid_hashes(tmp_path: Path) -> None:
    _manifest(tmp_path, "valid-set", "valid invalid-filter body")
    _manifest(tmp_path, "bad-set", "bad invalid-filter body")
    tampered = tmp_path / "bad-set" / "reviewed" / "spiritual-spell-0032.txt"
    tampered.write_text("tampered invalid-filter body", encoding="utf-8")

    inventory = list_benchmark_material_manifests(
        material_root=tmp_path,
        invalid_hashes_only=True,
    )

    assert inventory.invalid_hashes_only is True
    assert inventory.manifest_count == 1
    assert inventory.invalid_hash_count == 1
    assert inventory.verified_hash_count == 0
    assert inventory.hash_status_counts == {"mismatch": 1}
    assert inventory.manifests[0].collection_id == "bad-set"
    rendered = inventory.model_dump_json()
    assert "valid invalid-filter body" not in rendered
    assert "tampered invalid-filter body" not in rendered


def test_inventory_invalid_hashes_cli_json_is_prompt_safe(tmp_path: Path) -> None:
    _manifest(tmp_path, "valid-set", "valid invalid-cli body")
    _manifest(tmp_path, "bad-set", "bad invalid-cli body")
    tampered = tmp_path / "bad-set" / "reviewed" / "spiritual-spell-0032.txt"
    tampered.write_text("tampered invalid-cli body", encoding="utf-8")

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "list",
            "--material-root",
            str(tmp_path),
            "--invalid-hashes-only",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["invalid_hashes_only"] is True
    assert payload["manifest_count"] == 1
    assert payload["hash_status_counts"] == {"mismatch": 1}
    assert payload["manifests"][0]["collection_id"] == "bad-set"
    assert "valid invalid-cli body" not in result.output
    assert "tampered invalid-cli body" not in result.output


def test_inventory_invalid_hashes_cli_text_is_prompt_safe(tmp_path: Path) -> None:
    _manifest(tmp_path, "bad-set", "bad invalid-text body")
    tampered = tmp_path / "bad-set" / "reviewed" / "spiritual-spell-0032.txt"
    tampered.write_text("tampered invalid-text body", encoding="utf-8")

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "list",
            "--material-root",
            str(tmp_path),
            "--invalid-hashes-only",
        ],
    )

    assert result.exit_code == 0
    assert "Invalid hashes only: true" in result.output
    assert "Hash check: enabled" in result.output
    assert "bad-set" in result.output
    assert "tampered invalid-text body" not in result.output
