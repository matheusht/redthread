"""Tests for local replay target eligibility boundaries."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from redthread.benchmarks.material_inventory import list_benchmark_material_manifests
from redthread.benchmarks.material_review import import_reviewed_material
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures
from redthread.cli import main


def _import_nonlocal_seed(tmp_path: Path, text: str) -> None:
    fixture = next(item for item in load_spiritual_spell_fixtures() if item.id == "spiritual-spell-0032")
    source = tmp_path / "nonlocal-seed.txt"
    source.write_text(text, encoding="utf-8")
    import_reviewed_material(
        fixture,
        source_material_path=source,
        material_root=tmp_path,
        reviewed_by="security-review-owner",
        reviewed_at="2026-04-26T00:00:00Z",
        reviewer_ids=["security-review-owner", "benchmark-owner"],
        material_class="approved_replay_seed",
        allowed_target_ids=["staging-target"],
        allow_nonlocal_targets=True,
    )


def test_nonlocal_only_seed_is_not_local_replay_ready(tmp_path: Path) -> None:
    _import_nonlocal_seed(tmp_path, "nonlocal target inventory body")

    inventory = list_benchmark_material_manifests(material_root=tmp_path, verify_hashes=True)

    assert inventory.material_ready_count == 0
    assert inventory.material_blocked_count == 0
    assert inventory.engine_decision == "no_replay_ready"
    assert inventory.operator_next_step == "import approved replay seed before replay"
    assert inventory.suggested_replay_commands == []
    assert "nonlocal target inventory body" not in inventory.model_dump_json()


def test_replay_commands_only_does_not_emit_nonlocal_only_seed(tmp_path: Path) -> None:
    _import_nonlocal_seed(tmp_path, "nonlocal target command body")

    result = CliRunner().invoke(
        main,
        ["eval", "jailbreak-material", "list", "--material-root", str(tmp_path), "--replay-commands-only"],
    )

    assert result.exit_code == 0
    assert result.output == ""
    assert "nonlocal target command body" not in result.output
