"""Tests for prompt-safe material inventory filters."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from click.testing import CliRunner

from redthread.benchmarks.material_inventory import list_benchmark_material_manifests
from redthread.benchmarks.material_review import ReviewableMaterialClass, import_reviewed_material
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures
from redthread.cli import main


def _import_material(
    tmp_path: Path,
    *,
    collection_id: str,
    material_class: str,
    text: str,
    allowed_targets: list[str] | None = None,
) -> None:
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
        material_class=cast(ReviewableMaterialClass, material_class),
        allowed_target_ids=allowed_targets,
        collection_id=collection_id,
        allow_nonlocal_targets=True,
    )


def test_material_inventory_filters_by_material_class(tmp_path: Path) -> None:
    _import_material(
        tmp_path,
        collection_id="approved-set",
        material_class="approved_replay_seed",
        text="approved filter body",
    )
    _import_material(
        tmp_path,
        collection_id="redacted-set",
        material_class="redacted",
        text="redacted filter body",
    )

    inventory = list_benchmark_material_manifests(
        material_root=tmp_path,
        material_class="approved_replay_seed",
    )

    assert inventory.manifest_count == 1
    assert inventory.material_class == "approved_replay_seed"
    assert inventory.material_class_counts == {"approved_replay_seed": 1}
    assert inventory.manifests[0].manifest_ref.startswith("approved-set/")
    assert "approved filter body" not in inventory.model_dump_json()
    assert "redacted filter body" not in inventory.model_dump_json()


def test_material_inventory_filters_by_allowed_target(tmp_path: Path) -> None:
    _import_material(
        tmp_path,
        collection_id="local-set",
        material_class="approved_replay_seed",
        text="local target filter body",
        allowed_targets=["local-dev"],
    )
    _import_material(
        tmp_path,
        collection_id="staging-set",
        material_class="approved_replay_seed",
        text="staging target filter body",
        allowed_targets=["staging-target"],
    )

    inventory = list_benchmark_material_manifests(
        material_root=tmp_path,
        allowed_target_id="staging-target",
    )

    assert inventory.manifest_count == 1
    assert inventory.allowed_target_id == "staging-target"
    assert inventory.allowed_target_counts == {"staging-target": 1}
    assert inventory.manifests[0].manifest_ref.startswith("staging-set/")
    assert "local target filter body" not in inventory.model_dump_json()
    assert "staging target filter body" not in inventory.model_dump_json()


def test_material_inventory_cli_filters_are_prompt_safe(tmp_path: Path) -> None:
    _import_material(
        tmp_path,
        collection_id="approved-set",
        material_class="approved_replay_seed",
        text="approved cli filter body",
        allowed_targets=["local-dev"],
    )
    _import_material(
        tmp_path,
        collection_id="redacted-set",
        material_class="redacted",
        text="redacted cli filter body",
        allowed_targets=["staging-target"],
    )

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "list",
            "--material-root",
            str(tmp_path),
            "--material-class",
            "redacted",
            "--allowed-target",
            "staging-target",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["manifest_count"] == 1
    assert payload["material_class"] == "redacted"
    assert payload["allowed_target_id"] == "staging-target"
    assert payload["material_class_counts"] == {"redacted": 1}
    assert payload["allowed_target_counts"] == {"staging-target": 1}
    assert payload["manifests"][0]["manifest_ref"].startswith("redacted-set/")
    assert "approved cli filter body" not in result.output
    assert "redacted cli filter body" not in result.output
