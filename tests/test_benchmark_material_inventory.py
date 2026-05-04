"""Tests for prompt-safe benchmark material vault inventory."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from redthread.benchmarks.material_inventory import list_benchmark_material_manifests
from redthread.benchmarks.material_review import import_reviewed_material
from redthread.benchmarks.material_vault import MaterialVaultError
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures
from redthread.cli import main


def _manifest(tmp_path: Path, text: str = "toy inventory prompt body") -> str:
    fixture = next(
        item for item in load_spiritual_spell_fixtures()
        if item.id == "spiritual-spell-0032"
    )
    source = tmp_path / "reviewed-seed.txt"
    source.write_text(text, encoding="utf-8")
    result = import_reviewed_material(
        fixture,
        source_material_path=source,
        material_root=tmp_path,
        reviewed_by="security-review-owner",
        reviewed_at="2026-04-26T00:00:00Z",
        reviewer_ids=["security-review-owner", "benchmark-owner"],
        material_class="approved_replay_seed",
    )
    return result.manifest_ref


def test_lists_material_manifests_without_prompt_bodies(tmp_path: Path) -> None:
    _manifest(tmp_path, "toy inventory helper body")

    inventory = list_benchmark_material_manifests(material_root=tmp_path)
    rendered = inventory.model_dump_json()

    assert inventory.manifest_count == 1
    assert inventory.manifests[0].fixture_id == "spiritual-spell-0032"
    assert inventory.manifests[0].hash_verified is False
    assert inventory.manifests[0].hash_status == "not_checked"
    assert inventory.verified_hash_count == 0
    assert inventory.invalid_hash_count == 0
    assert "toy inventory helper body" not in rendered
    assert "not read" in inventory.raw_prompt_policy


def test_lists_material_manifests_with_hash_verification(tmp_path: Path) -> None:
    _manifest(tmp_path, "toy inventory hash body")

    inventory = list_benchmark_material_manifests(material_root=tmp_path, verify_hashes=True)

    assert inventory.manifests[0].hash_verified is True
    assert inventory.manifests[0].hash_status == "verified"
    assert inventory.verified_hash_count == 1
    assert inventory.invalid_hash_count == 0
    assert "toy inventory hash body" not in inventory.model_dump_json()


def test_lists_material_manifests_with_hash_mismatch_status(tmp_path: Path) -> None:
    _manifest(tmp_path, "toy inventory mismatch body")
    material_path = tmp_path / "spiritual-spell" / "reviewed" / "spiritual-spell-0032.txt"
    material_path.write_text("tampered inventory body", encoding="utf-8")

    inventory = list_benchmark_material_manifests(material_root=tmp_path, verify_hashes=True)

    assert inventory.manifests[0].hash_verified is False
    assert inventory.manifests[0].hash_status == "mismatch"
    assert inventory.verified_hash_count == 0
    assert inventory.invalid_hash_count == 1
    assert "tampered inventory body" not in inventory.model_dump_json()


def test_lists_material_manifests_by_safe_collection(tmp_path: Path) -> None:
    manifest_ref = _manifest(tmp_path)

    inventory = list_benchmark_material_manifests(
        material_root=tmp_path,
        collection_id="spiritual-spell",
    )

    assert [row.manifest_ref for row in inventory.manifests] == [manifest_ref]


def test_rejects_unsafe_inventory_collection_id(tmp_path: Path) -> None:
    with pytest.raises(MaterialVaultError, match="safe slug"):
        list_benchmark_material_manifests(material_root=tmp_path, collection_id="../vault")


def test_material_inventory_cli_json_is_prompt_safe(tmp_path: Path) -> None:
    _manifest(tmp_path, "toy inventory cli body")

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "list",
            "--material-root",
            str(tmp_path),
            "--verify-hashes",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["manifest_count"] == 1
    assert payload["verified_hash_count"] == 1
    assert payload["manifests"][0]["fixture_id"] == "spiritual-spell-0032"
    assert payload["manifests"][0]["hash_status"] == "verified"
    assert "toy inventory cli body" not in result.output


def test_material_inventory_cli_text_is_prompt_safe(tmp_path: Path) -> None:
    _manifest(tmp_path, "toy inventory text body")

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "list",
            "--material-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "REDTHREAD BENCHMARK MATERIAL INVENTORY" in result.output
    assert "Manifest count: 1" in result.output
    assert "Hash check: not checked" in result.output
    assert "Raw prompt bodies: not read" in result.output
    assert "spiritual-spell-0032" in result.output
    assert "toy inventory text body" not in result.output
