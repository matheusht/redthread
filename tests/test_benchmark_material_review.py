"""Tests for human-reviewed benchmark material import and approval."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from redthread.benchmarks.jailbreak_fixtures import (
    JAILBREAK_FIXTURE_SCHEMA_VERSION,
    JailbreakBenchmarkFixture,
    load_jailbreak_fixture_pack,
)
from redthread.benchmarks.material_review import (
    MaterialReviewError,
    approve_fixture_for_replay,
    import_reviewed_material,
)
from redthread.benchmarks.material_vault import load_material_manifest, resolve_reviewed_material


def _fixture(**overrides: object) -> JailbreakBenchmarkFixture:
    fixture: dict[str, object] = {
        "id": "spiritual-spell-0032",
        "source_repo": "https://github.com/Goochbeater/Spiritual-Spell-Red-Teaming",
        "source_path": "Jailbreak-Guide/Anthropic/Opus 4.7/ENI Writer ✒️.md",
        "source_commit": "pin-before-use",
        "license_status": "unknown",
        "provenance_status": "unverified",
        "family": "eni_variants",
        "target_family": "anthropic_claude",
        "risk_plugin_id": "prompt_injection",
        "strategy_id": "static_seed_replay",
        "rubric_id": "authorization_bypass",
        "prompt_material_class": "metadata_only",
        "prompt_material_ref": "not-copied",
        "safety_level": "high",
        "review_status": "pending",
        "expected_safe_behavior": "keep trusted instructions above adversarial framing",
    }
    fixture.update(overrides)
    pack = {"schema_version": JAILBREAK_FIXTURE_SCHEMA_VERSION, "fixtures": [fixture]}
    return load_jailbreak_fixture_pack(pack)[0]


def _source_file(tmp_path: Path, text: str = "toy reviewed local-only seed") -> Path:
    source = tmp_path / "source.txt"
    source.write_text(text, encoding="utf-8")
    return source


def test_imports_redacted_material_for_reference(tmp_path: Path) -> None:
    fixture = _fixture()
    source = _source_file(tmp_path)

    result = import_reviewed_material(
        fixture,
        source_material_path=source,
        material_root=tmp_path,
        reviewed_by="security-reviewer",
        reviewed_at="2026-04-26T00:00:00Z",
    )

    assert result.material_ref == "spiritual-spell/redacted/spiritual-spell-0032.txt"
    assert result.manifest.material_class == "redacted"
    assert result.manifest.review_status == "redacted"
    assert (tmp_path / result.material_ref).read_text(encoding="utf-8") == source.read_text(
        encoding="utf-8"
    )


def test_imports_manifest_json_with_hash(tmp_path: Path) -> None:
    fixture = _fixture()
    source = _source_file(tmp_path)

    result = import_reviewed_material(
        fixture,
        source_material_path=source,
        material_root=tmp_path,
        reviewed_by="security-reviewer",
        reviewed_at="2026-04-26T00:00:00Z",
    )
    manifest_path = tmp_path / result.manifest_ref
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest_data["fixture_id"] == fixture.id
    assert manifest_data["sha256"] == result.manifest.sha256
    assert load_material_manifest(result.manifest_ref, material_root=tmp_path) == result.manifest


def test_approves_fixture_for_replay_from_approved_manifest(tmp_path: Path) -> None:
    fixture = _fixture()
    source = _source_file(tmp_path)
    result = import_reviewed_material(
        fixture,
        source_material_path=source,
        material_root=tmp_path,
        reviewed_by="security-reviewer",
        reviewed_at="2026-04-26T00:00:00Z",
        reviewer_ids=["security-reviewer", "benchmark-owner"],
        material_class="approved_replay_seed",
    )

    approved = approve_fixture_for_replay(fixture, result.manifest)
    material = resolve_reviewed_material(
        approved,
        manifest_ref=result.manifest_ref,
        material_root=tmp_path,
        target_id="local-dev",
    )

    assert approved.is_executable is True
    assert approved.prompt_material_ref == result.material_ref
    assert result.manifest.reviewers == ["benchmark-owner", "security-reviewer"]
    assert material.text == "toy reviewed local-only seed"


def test_rejects_approved_replay_seed_without_two_reviewers(tmp_path: Path) -> None:
    fixture = _fixture()
    source = _source_file(tmp_path)

    with pytest.raises(MaterialReviewError, match="two distinct reviewers"):
        import_reviewed_material(
            fixture,
            source_material_path=source,
            material_root=tmp_path,
            reviewed_by="security-reviewer",
            reviewed_at="2026-04-26T00:00:00Z",
            material_class="approved_replay_seed",
        )


def test_rejects_duplicate_approved_replay_seed_reviewer(tmp_path: Path) -> None:
    fixture = _fixture()
    source = _source_file(tmp_path)

    with pytest.raises(MaterialReviewError, match="two distinct reviewers"):
        import_reviewed_material(
            fixture,
            source_material_path=source,
            material_root=tmp_path,
            reviewed_by="security-reviewer",
            reviewed_at="2026-04-26T00:00:00Z",
            reviewer_ids=["security-reviewer"],
            material_class="approved_replay_seed",
        )


def test_rejects_nonlocal_target_import_without_override(tmp_path: Path) -> None:
    fixture = _fixture()
    source = _source_file(tmp_path)

    with pytest.raises(MaterialReviewError, match="explicit override"):
        import_reviewed_material(
            fixture,
            source_material_path=source,
            material_root=tmp_path,
            reviewed_by="security-reviewer",
            reviewed_at="2026-04-26T00:00:00Z",
            reviewer_ids=["security-reviewer", "benchmark-owner"],
            material_class="approved_replay_seed",
            allowed_target_ids=["prod-model"],
        )


def test_rejects_redacted_manifest_promotion(tmp_path: Path) -> None:
    fixture = _fixture()
    source = _source_file(tmp_path)
    result = import_reviewed_material(
        fixture,
        source_material_path=source,
        material_root=tmp_path,
        reviewed_by="security-reviewer",
        reviewed_at="2026-04-26T00:00:00Z",
    )

    with pytest.raises(MaterialReviewError, match="approved replay seed"):
        approve_fixture_for_replay(fixture, result.manifest)


def test_rejects_unsafe_collection_id(tmp_path: Path) -> None:
    fixture = _fixture()
    source = _source_file(tmp_path)

    with pytest.raises(MaterialReviewError, match="safe slug"):
        import_reviewed_material(
            fixture,
            source_material_path=source,
            material_root=tmp_path,
            reviewed_by="security-reviewer",
            reviewed_at="2026-04-26T00:00:00Z",
            collection_id="../spiritual-spell",
        )
