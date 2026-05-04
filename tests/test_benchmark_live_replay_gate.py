"""Tests for deferred live benchmark replay gating."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from redthread.benchmarks.material_review import import_reviewed_material
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures
from redthread.cli import main


def _manifest(tmp_path: Path) -> str:
    fixture = next(
        item for item in load_spiritual_spell_fixtures()
        if item.id == "spiritual-spell-0032"
    )
    source = tmp_path / "reviewed-seed.txt"
    source.write_text("toy approved deferred replay seed", encoding="utf-8")
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


def test_cli_replay_blocks_live_target_even_with_legacy_flag(tmp_path: Path) -> None:
    manifest_ref = _manifest(tmp_path)

    result = CliRunner().invoke(
        main,
        [
            "eval",
            "jailbreak-corpus",
            "--fixture-id",
            "spiritual-spell-0032",
            "--replay",
            "--manifest-ref",
            manifest_ref,
            "--material-root",
            str(tmp_path),
            "--target",
            "prod-model",
            "--allow-live-target",
        ],
    )

    assert result.exit_code != 0
    assert "live benchmark replay is deferred" in result.output
    assert "typed" in result.output
    assert "acknowledgement" in result.output
    assert "toy approved deferred replay seed" not in result.output
