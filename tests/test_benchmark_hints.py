"""Tests for safe benchmark persona and strategy hints."""

from __future__ import annotations

from redthread.benchmarks.hints import build_fixture_hint_profile, build_fixture_hint_profiles
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures


def test_eni_writer_fixture_maps_to_persona_engineering_axes() -> None:
    fixtures = load_spiritual_spell_fixtures()
    fixture = next(item for item in fixtures if "ENI Writer" in item.source_path)

    profile = build_fixture_hint_profile(fixture)

    assert profile.fixture_id == fixture.id
    assert "eni_writer" not in profile.persona_axes
    assert "relational_persona_pressure" in profile.persona_axes
    assert "guardrail_rebuttal_resilience" in profile.persona_axes
    assert "reasoning_channel_boundary" in profile.persona_axes
    assert "docs/wiki/entities/eni-writer-persona.md" in profile.source_references


def test_peeling_onions_tags_map_to_tap_and_crescendo_hints() -> None:
    fixtures = load_spiritual_spell_fixtures()
    fixture = next(item for item in fixtures if "ENI Writer" in item.source_path)

    profile = build_fixture_hint_profile(fixture)

    assert "static_seed_replay" in profile.recommended_strategy_ids
    assert "crescendo" in profile.recommended_strategy_ids
    assert "tap" in profile.recommended_strategy_ids
    assert "fiction_wrapped_policy_bypass" in profile.judge_focus
    assert "safety_instruction_rebuttal" in profile.judge_focus
    assert "docs/wiki/concepts/peeling-onions.md" in profile.source_references


def test_system_prompt_records_focus_on_sensitive_disclosure() -> None:
    fixtures = load_spiritual_spell_fixtures()
    fixture = next(item for item in fixtures if item.risk_plugin_id == "system_prompt_leakage")

    profile = build_fixture_hint_profile(fixture)

    assert profile.recommended_strategy_ids == ["static_seed_replay"]
    assert "sensitive_instruction_disclosure" in profile.judge_focus


def test_builds_hint_profiles_for_fixture_collection() -> None:
    fixtures = load_spiritual_spell_fixtures()[:3]

    profiles = build_fixture_hint_profiles(fixtures)

    assert [profile.fixture_id for profile in profiles] == [fixture.id for fixture in fixtures]
    assert all(profile.summary_lines()[0].startswith("Fixture:") for profile in profiles)
