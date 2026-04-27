"""Tests for Spiritual Spell jailbreak benchmark fixture contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from redthread.benchmarks.jailbreak_fixtures import (
    JAILBREAK_FIXTURE_SCHEMA_VERSION,
    JailbreakFixtureError,
    load_jailbreak_fixture_file,
    load_jailbreak_fixture_pack,
)


def _fixture(**overrides: object) -> dict[str, object]:
    fixture: dict[str, object] = {
        "id": "spiritual-spell-0001",
        "source_repo": "https://github.com/Goochbeater/Spiritual-Spell-Red-Teaming",
        "source_path": "Jailbreak-Guide/System Prompts/example.md",
        "source_commit": "pin-before-use",
        "license_status": "unknown",
        "provenance_status": "unverified",
        "family": "system_prompt_leakage",
        "target_family": "anthropic_claude",
        "risk_plugin_id": "system_prompt_leakage",
        "strategy_id": "static_seed_replay",
        "rubric_id": "sensitive_info",
        "prompt_material_class": "metadata_only",
        "prompt_material_ref": "not-copied",
        "safety_level": "high",
        "review_status": "pending",
        "expected_safe_behavior": "refuse to reveal hidden system instructions",
        "technique_tags": ["narrative_embedding"],
        "persona_tags": ["eni_writer"],
        "attack_layers": ["persona_modulation"],
        "reference_pages": ["docs/wiki/entities/eni-writer-persona.md"],
        "raw_prompt_required": True,
        "notes": "metadata only",
    }
    fixture.update(overrides)
    return fixture


def _pack(*fixtures: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": JAILBREAK_FIXTURE_SCHEMA_VERSION,
        "fixtures": list(fixtures),
    }


def test_loads_valid_metadata_only_fixture() -> None:
    fixtures = load_jailbreak_fixture_pack(_pack(_fixture()))

    assert len(fixtures) == 1
    fixture = fixtures[0]
    assert fixture.id == "spiritual-spell-0001"
    assert fixture.is_executable is False
    assert fixture.prompt_material_ref == "not-copied"


def test_fixture_lineage_metadata_is_trace_safe() -> None:
    fixture = load_jailbreak_fixture_pack(_pack(_fixture()))[0]

    metadata = fixture.lineage_metadata()

    assert metadata["benchmark_fixture_id"] == "spiritual-spell-0001"
    assert metadata["benchmark_source_path"].endswith("example.md")
    assert metadata["benchmark_prompt_material_class"] == "metadata_only"
    assert metadata["benchmark_technique_tags"] == "narrative_embedding"
    assert metadata["benchmark_persona_tags"] == "eni_writer"
    assert metadata["benchmark_attack_layers"] == "persona_modulation"
    assert metadata["benchmark_raw_prompt_required"] == "true"
    assert "expected_safe_behavior" not in metadata


def test_rejects_missing_source_lineage() -> None:
    fixture = _fixture(source_path="")

    with pytest.raises(JailbreakFixtureError, match="invalid jailbreak benchmark fixture"):
        load_jailbreak_fixture_pack(_pack(fixture))


def test_rejects_unknown_prompt_material_class() -> None:
    fixture = _fixture(prompt_material_class="raw_prompt_dump")

    with pytest.raises(JailbreakFixtureError, match="invalid jailbreak benchmark fixture"):
        load_jailbreak_fixture_pack(_pack(fixture))


def test_rejects_approved_seed_without_review_status() -> None:
    fixture = _fixture(
        prompt_material_class="approved_replay_seed",
        prompt_material_ref="fixtures/reviewed/spiritual-spell-0001.txt",
        review_status="pending",
    )

    with pytest.raises(JailbreakFixtureError, match="invalid jailbreak benchmark fixture"):
        load_jailbreak_fixture_pack(_pack(fixture))


def test_rejects_approved_seed_without_material_reference() -> None:
    fixture = _fixture(
        prompt_material_class="approved_replay_seed",
        review_status="approved_replay_seed",
    )

    with pytest.raises(JailbreakFixtureError, match="invalid jailbreak benchmark fixture"):
        load_jailbreak_fixture_pack(_pack(fixture))


def test_approved_replay_seed_is_executable_after_review() -> None:
    fixture = _fixture(
        prompt_material_class="approved_replay_seed",
        prompt_material_ref="fixtures/reviewed/spiritual-spell-0001.txt",
        review_status="approved_replay_seed",
    )

    loaded = load_jailbreak_fixture_pack(_pack(fixture))[0]

    assert loaded.is_executable is True


def test_rejects_duplicate_fixture_ids() -> None:
    with pytest.raises(JailbreakFixtureError, match="duplicate jailbreak fixture id"):
        load_jailbreak_fixture_pack(_pack(_fixture(), _fixture()))


def test_rejects_unknown_pack_schema() -> None:
    pack = {"schema_version": "other", "fixtures": []}

    with pytest.raises(JailbreakFixtureError, match="unknown jailbreak fixture schema version"):
        load_jailbreak_fixture_pack(pack)


def test_loads_fixture_file(tmp_path: Path) -> None:
    path = tmp_path / "fixtures.json"
    path.write_text(json.dumps(_pack(_fixture())), encoding="utf-8")

    fixtures = load_jailbreak_fixture_file(path)

    assert [fixture.id for fixture in fixtures] == ["spiritual-spell-0001"]
