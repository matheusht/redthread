"""Tests for replay-command eligibility boundaries."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from click.testing import CliRunner

from redthread.benchmarks.material_inventory import list_benchmark_material_manifests
from redthread.benchmarks.material_review import ReviewableMaterialClass, import_reviewed_material
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures
from redthread.cli import main


def _import_material(tmp_path: Path, *, material_class: str, text: str) -> None:
    fixture = next(item for item in load_spiritual_spell_fixtures() if item.id == "spiritual-spell-0032")
    source = tmp_path / f"{material_class}.txt"
    source.write_text(text, encoding="utf-8")
    import_reviewed_material(
        fixture,
        source_material_path=source,
        material_root=tmp_path,
        reviewed_by="security-review-owner",
        reviewed_at="2026-04-26T00:00:00Z",
        reviewer_ids=["security-review-owner", "benchmark-owner"],
        material_class=cast(ReviewableMaterialClass, material_class),
        collection_id=f"{material_class}-set",
    )


def test_redacted_material_is_not_replay_ready(tmp_path: Path) -> None:
    _import_material(tmp_path, material_class="redacted", text="redacted replay eligibility body")

    inventory = list_benchmark_material_manifests(material_root=tmp_path, verify_hashes=True)

    assert inventory.material_ready_count == 0
    assert inventory.engine_decision == "no_replay_ready"
    assert inventory.operator_next_step == "import approved replay seed before replay"
    assert inventory.operator_summary == "ready=0; blocked=0; import approved replay seed"
    assert inventory.suggested_replay_commands == []
    assert "redacted replay eligibility body" not in inventory.model_dump_json()


def test_replay_commands_only_does_not_emit_redacted_material(tmp_path: Path) -> None:
    _import_material(tmp_path, material_class="redacted", text="redacted command eligibility body")

    result = CliRunner().invoke(
        main,
        ["eval", "jailbreak-material", "list", "--material-root", str(tmp_path), "--replay-commands-only"],
    )

    assert result.exit_code == 0
    assert result.output == ""
    assert "redacted command eligibility body" not in result.output
