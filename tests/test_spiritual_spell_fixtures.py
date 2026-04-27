"""Tests for the Spiritual Spell metadata fixture pack."""

from __future__ import annotations

from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures


def test_spiritual_spell_pack_loads_full_metadata_only_inventory() -> None:
    fixtures = load_spiritual_spell_fixtures()

    assert len(fixtures) == 210
    assert all(fixture.prompt_material_class == "metadata_only" for fixture in fixtures)
    assert all(fixture.review_status == "pending" for fixture in fixtures)
    assert all(fixture.prompt_material_ref == "not-copied" for fixture in fixtures)
    assert all(not fixture.is_executable for fixture in fixtures)


def test_spiritual_spell_pack_has_stable_ids_and_source_paths() -> None:
    fixtures = load_spiritual_spell_fixtures()

    assert fixtures[0].id == "spiritual-spell-0001"
    assert fixtures[0].source_path == (
        "Jailbreak-Guide/Anthropic/Amazon's Rufus/ALL Rufus Tools Full JSON.md"
    )
    assert fixtures[-1].id == "spiritual-spell-0210"
    assert fixtures[-1].source_path == "README.md"
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

    families = {fixture.family for fixture in fixtures}
    assert "agent_injection" in families
    assert "document_based" in families
    assert "eni_lime" in families
    assert "model_specific_base_jailbreaks" in families
    assert "policy_jailbreak" in families
    assert "system_prompt_tool_schema_captures" in families
    assert "readme_directory_notes" in families


def test_spiritual_spell_pack_adds_safe_semantic_tags() -> None:
    fixtures = load_spiritual_spell_fixtures()
    eni_fixture = next(fixture for fixture in fixtures if "ENI Writer" in fixture.source_path)

    assert eni_fixture.raw_prompt_required is True
    assert "eni_writer" in eni_fixture.persona_tags
    assert "narrative_embedding" in eni_fixture.technique_tags
    assert "guardrail_rebuttal" in eni_fixture.attack_layers
    assert "docs/wiki/entities/eni-writer-persona.md" in eni_fixture.reference_pages
    assert "docs/wiki/concepts/peeling-onions.md" in eni_fixture.reference_pages


def test_readme_records_do_not_require_raw_prompt_material() -> None:
    fixtures = load_spiritual_spell_fixtures()
    readme_fixture = next(fixture for fixture in fixtures if fixture.source_path == "README.md")

    assert readme_fixture.family == "readme_directory_notes"
    assert readme_fixture.raw_prompt_required is False
