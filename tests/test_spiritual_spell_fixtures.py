"""Tests for the Spiritual Spell metadata fixture pack."""

from __future__ import annotations

from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures


def test_spiritual_spell_pack_loads_metadata_only_records() -> None:
    fixtures = load_spiritual_spell_fixtures()

    assert len(fixtures) == 7
    assert all(fixture.prompt_material_class == "metadata_only" for fixture in fixtures)
    assert all(fixture.review_status == "pending" for fixture in fixtures)
    assert all(fixture.prompt_material_ref == "not-copied" for fixture in fixtures)
    assert all(not fixture.is_executable for fixture in fixtures)


def test_spiritual_spell_pack_has_stable_ids_and_source_paths() -> None:
    fixtures = load_spiritual_spell_fixtures()

    assert [fixture.id for fixture in fixtures] == [
        "spiritual-spell-0001",
        "spiritual-spell-0002",
        "spiritual-spell-0003",
        "spiritual-spell-0004",
        "spiritual-spell-0005",
        "spiritual-spell-0006",
        "spiritual-spell-0007",
    ]
    assert all(fixture.source_path.startswith("Jailbreak-Guide/") for fixture in fixtures)
    assert all(fixture.source_commit == "pin-before-use" for fixture in fixtures)


def test_spiritual_spell_pack_maps_to_redthread_risks_and_strategies() -> None:
    fixtures = load_spiritual_spell_fixtures()

    assert {fixture.risk_plugin_id for fixture in fixtures} == {
        "prompt_injection",
        "system_prompt_leakage",
        "unsafe_tool_use",
    }
    assert {fixture.strategy_id for fixture in fixtures} == {"static_seed_replay"}
    assert {fixture.rubric_id for fixture in fixtures} == {
        "authorization_bypass",
        "sensitive_info",
    }


def test_spiritual_spell_pack_covers_planned_method_families() -> None:
    fixtures = load_spiritual_spell_fixtures()

    assert {fixture.family for fixture in fixtures} == {
        "agent_injection",
        "document_based",
        "eni_lime",
        "model_specific_base_jailbreak",
        "policy_bypass",
        "system_prompt_leakage",
    }
