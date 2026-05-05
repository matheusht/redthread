"""Tests for optional material inventory hash check skipping."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from redthread.benchmarks.material_review import import_reviewed_material
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures
from redthread.cli import main


def _manifest(tmp_path: Path, text: str = "toy skip hash prompt body") -> None:
    fixture = next(
        item for item in load_spiritual_spell_fixtures()
        if item.id == "spiritual-spell-0032"
    )
    source = tmp_path / "reviewed-seed.txt"
    source.write_text(text, encoding="utf-8")
    import_reviewed_material(
        fixture,
        source_material_path=source,
        material_root=tmp_path,
        reviewed_by="security-review-owner",
        reviewed_at="2026-04-26T00:00:00Z",
        reviewer_ids=["security-review-owner", "benchmark-owner"],
        material_class="approved_replay_seed",
    )


def test_material_inventory_cli_can_skip_default_hash_check(tmp_path: Path) -> None:
    _manifest(tmp_path, "skip hash cli body")

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-material",
            "list",
            "--material-root",
            str(tmp_path),
            "--skip-hash-check",
        ],
    )

    assert result.exit_code == 0
    assert "Hash check: not checked" in result.output
    assert "Engine decision: needs_hash_check" in result.output
    assert "Ready materials: 0" in result.output
    assert "skip hash cli body" not in result.output
