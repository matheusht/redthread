"""Tests for prompt-safe benchmark material verification helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from redthread.benchmarks.material_review import import_reviewed_material
from redthread.benchmarks.material_vault import MaterialVaultError
from redthread.benchmarks.material_verify import verify_benchmark_material_manifest
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures


def _manifest(tmp_path: Path, text: str = "toy helper verify material") -> str:
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


def test_verify_material_manifest_returns_prompt_safe_payload(tmp_path: Path) -> None:
    manifest_ref = _manifest(tmp_path, "toy helper prompt body")

    verification = verify_benchmark_material_manifest(manifest_ref, material_root=tmp_path)
    rendered = verification.model_dump_json()

    assert verification.fixture_id == "spiritual-spell-0032"
    assert verification.hash_verified is True
    assert verification.reviewers == ["benchmark-owner", "security-review-owner"]
    assert "toy helper prompt body" not in rendered
    assert "private benchmark vault" in verification.raw_prompt_policy


def test_verify_material_manifest_rejects_tampered_material(tmp_path: Path) -> None:
    manifest_ref = _manifest(tmp_path)
    material_path = tmp_path / "spiritual-spell" / "reviewed" / "spiritual-spell-0032.txt"
    material_path.write_text("tampered helper body", encoding="utf-8")

    with pytest.raises(MaterialVaultError, match="hash does not match"):
        verify_benchmark_material_manifest(manifest_ref, material_root=tmp_path)
