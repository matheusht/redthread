"""Tests for prompt-safe material inventory limits."""

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


def _import_material(tmp_path: Path, *, collection_id: str, text: str) -> None:
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


def test_material_inventory_limit_is_prompt_safe(tmp_path: Path) -> None:
    _import_material(tmp_path, collection_id="alpha-set", text="alpha limit body")
    _import_material(tmp_path, collection_id="beta-set", text="beta limit body")

    inventory = list_benchmark_material_manifests(material_root=tmp_path, limit=1)

    assert inventory.limit == 1
    assert inventory.manifest_count == 1
    assert len(inventory.manifests) == 1
    assert inventory.manifests[0].collection_id == "alpha-set"
    assert "alpha limit body" not in inventory.model_dump_json()
    assert "beta limit body" not in inventory.model_dump_json()


def test_material_inventory_rejects_invalid_limit(tmp_path: Path) -> None:
    with pytest.raises(MaterialVaultError, match="limit must be at least 1"):
        list_benchmark_material_manifests(material_root=tmp_path, limit=0)


def test_material_inventory_cli_limit_is_prompt_safe(tmp_path: Path) -> None:
    _import_material(tmp_path, collection_id="alpha-set", text="alpha cli limit body")
    _import_material(tmp_path, collection_id="beta-set", text="beta cli limit body")

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "list",
            "--material-root",
            str(tmp_path),
            "--limit",
            "1",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["limit"] == 1
    assert payload["manifest_count"] == 1
    assert len(payload["manifests"]) == 1
    assert payload["manifests"][0]["collection_id"] == "alpha-set"
    assert "alpha cli limit body" not in result.output
    assert "beta cli limit body" not in result.output
