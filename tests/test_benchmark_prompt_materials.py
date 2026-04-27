"""Tests for reviewed benchmark prompt material loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from redthread.benchmarks.jailbreak_fixtures import (
    JAILBREAK_FIXTURE_SCHEMA_VERSION,
    JailbreakBenchmarkFixture,
    load_jailbreak_fixture_pack,
)
from redthread.benchmarks.prompt_materials import (
    PromptMaterialError,
    load_prompt_material,
    load_replay_seed_prompts,
)


def _fixture(**overrides: object) -> JailbreakBenchmarkFixture:
    fixture: dict[str, object] = {
        "id": "spiritual-spell-0001",
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


def test_metadata_only_fixture_has_no_prompt_material() -> None:
    fixture = _fixture()

    with pytest.raises(PromptMaterialError, match="metadata-only"):
        load_prompt_material(fixture, material_root="fixtures")


def test_loads_redacted_material_for_reference(tmp_path: Path) -> None:
    material_path = tmp_path / "redacted" / "spiritual-spell-0001.txt"
    material_path.parent.mkdir()
    material_path.write_text("[redacted benchmark reference]", encoding="utf-8")
    fixture = _fixture(
        prompt_material_class="redacted",
        prompt_material_ref="redacted/spiritual-spell-0001.txt",
        review_status="redacted",
    )

    material = load_prompt_material(fixture, material_root=tmp_path)

    assert material.text == "[redacted benchmark reference]"
    assert material.may_execute is False


def test_loads_approved_replay_seed_prompts(tmp_path: Path) -> None:
    material_path = tmp_path / "reviewed" / "spiritual-spell-0001.txt"
    material_path.parent.mkdir()
    material_path.write_text("reviewed local-only seed", encoding="utf-8")
    fixture = _fixture(
        prompt_material_class="approved_replay_seed",
        prompt_material_ref="reviewed/spiritual-spell-0001.txt",
        review_status="approved_replay_seed",
    )

    prompts = load_replay_seed_prompts(fixture, material_root=tmp_path)

    assert prompts == ["reviewed local-only seed"]


def test_rejects_replay_for_non_executable_material(tmp_path: Path) -> None:
    fixture = _fixture(
        prompt_material_class="redacted",
        prompt_material_ref="redacted/spiritual-spell-0001.txt",
        review_status="redacted",
    )

    with pytest.raises(PromptMaterialError, match="approved replay seed"):
        load_replay_seed_prompts(fixture, material_root=tmp_path)


def test_rejects_material_path_traversal(tmp_path: Path) -> None:
    fixture = _fixture(
        prompt_material_class="redacted",
        prompt_material_ref="../outside.txt",
        review_status="redacted",
    )

    with pytest.raises(PromptMaterialError, match="escapes material root"):
        load_prompt_material(fixture, material_root=tmp_path)
