"""Tests for reviewed benchmark material manifests and vault resolution."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from redthread.benchmarks.jailbreak_fixtures import (
    JAILBREAK_FIXTURE_SCHEMA_VERSION,
    JailbreakBenchmarkFixture,
    load_jailbreak_fixture_pack,
)
from redthread.benchmarks.material_vault import (
    BENCHMARK_MATERIAL_ROOT_ENV,
    MATERIAL_MANIFEST_SCHEMA_VERSION,
    MaterialVaultError,
    benchmark_material_root,
    load_material_manifest,
    resolve_reviewed_material,
)


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
        "prompt_material_class": "approved_replay_seed",
        "prompt_material_ref": "spiritual-spell/reviewed/spiritual-spell-0032.txt",
        "safety_level": "high",
        "review_status": "approved_replay_seed",
        "expected_safe_behavior": "keep trusted instructions above adversarial framing",
    }
    fixture.update(overrides)
    pack = {"schema_version": JAILBREAK_FIXTURE_SCHEMA_VERSION, "fixtures": [fixture]}
    return load_jailbreak_fixture_pack(pack)[0]


def _write_material(root: Path, text: str = "toy reviewed local-only seed") -> str:
    material_path = root / "spiritual-spell" / "reviewed" / "spiritual-spell-0032.txt"
    material_path.parent.mkdir(parents=True)
    material_path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_manifest(root: Path, **overrides: object) -> None:
    manifest: dict[str, object] = {
        "schema_version": MATERIAL_MANIFEST_SCHEMA_VERSION,
        "fixture_id": "spiritual-spell-0032",
        "material_ref": "spiritual-spell/reviewed/spiritual-spell-0032.txt",
        "sha256": _write_material(root),
        "material_class": "approved_replay_seed",
        "review_status": "approved_replay_seed",
        "reviewed_by": "security-reviewer",
        "reviewed_at": "2026-04-26T00:00:00Z",
        "allowed_target_ids": ["local-dev"],
        "source_path": "Jailbreak-Guide/Anthropic/Opus 4.7/ENI Writer ✒️.md",
        "source_commit": "pin-before-use",
    }
    manifest.update(overrides)
    manifest_path = root / "spiritual-spell" / "manifests" / "spiritual-spell-0032.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


def test_material_root_uses_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(BENCHMARK_MATERIAL_ROOT_ENV, str(tmp_path))

    assert benchmark_material_root() == tmp_path.resolve()


def test_material_root_requires_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(BENCHMARK_MATERIAL_ROOT_ENV, raising=False)

    with pytest.raises(MaterialVaultError, match="REDTHREAD_BENCHMARK_MATERIAL_ROOT"):
        benchmark_material_root()


def test_loads_material_manifest_from_vault(tmp_path: Path) -> None:
    _write_manifest(tmp_path)

    manifest = load_material_manifest(
        "spiritual-spell/manifests/spiritual-spell-0032.json",
        material_root=tmp_path,
    )

    assert manifest.fixture_id == "spiritual-spell-0032"
    assert manifest.allowed_target_ids == ["local-dev"]


def test_resolves_reviewed_material_when_manifest_hash_matches(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    fixture = _fixture()

    material = resolve_reviewed_material(
        fixture,
        manifest_ref="spiritual-spell/manifests/spiritual-spell-0032.json",
        material_root=tmp_path,
        target_id="local-dev",
    )

    assert material.text == "toy reviewed local-only seed"
    assert material.may_execute is True


def test_blocks_material_hash_mismatch(tmp_path: Path) -> None:
    _write_manifest(tmp_path, sha256="0" * 64)
    fixture = _fixture()

    with pytest.raises(MaterialVaultError, match="hash does not match"):
        resolve_reviewed_material(
            fixture,
            manifest_ref="spiritual-spell/manifests/spiritual-spell-0032.json",
            material_root=tmp_path,
        )


def test_blocks_disallowed_target_for_executable_material(tmp_path: Path) -> None:
    _write_manifest(tmp_path, allowed_target_ids=["sandbox-only"])
    fixture = _fixture()

    with pytest.raises(MaterialVaultError, match="target is not allowed"):
        resolve_reviewed_material(
            fixture,
            manifest_ref="spiritual-spell/manifests/spiritual-spell-0032.json",
            material_root=tmp_path,
            target_id="local-dev",
        )


def test_blocks_manifest_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(MaterialVaultError, match="escapes material root"):
        load_material_manifest("../manifest.json", material_root=tmp_path)


def test_blocks_manifest_fixture_mismatch(tmp_path: Path) -> None:
    _write_manifest(tmp_path, fixture_id="other-fixture")
    fixture = _fixture()

    with pytest.raises(MaterialVaultError, match="fixture id does not match"):
        resolve_reviewed_material(
            fixture,
            manifest_ref="spiritual-spell/manifests/spiritual-spell-0032.json",
            material_root=tmp_path,
        )
