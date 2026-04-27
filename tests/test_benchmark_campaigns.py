"""Tests for benchmark fixture to campaign planning bridge."""

from __future__ import annotations

import pytest

from redthread.benchmarks.campaigns import build_benchmark_campaign_draft
from redthread.benchmarks.jailbreak_fixtures import JailbreakBenchmarkFixture
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures
from redthread.orchestration.campaign_planning import CampaignPlanningError


def _approved_fixture(index: int = 0) -> JailbreakBenchmarkFixture:
    fixture = load_spiritual_spell_fixtures()[index]
    return fixture.model_copy(
        update={
            "prompt_material_class": "approved_replay_seed",
            "prompt_material_ref": f"fixtures/reviewed/{fixture.id}.txt",
            "review_status": "approved_replay_seed",
        }
    )


def test_metadata_only_fixtures_cannot_plan_execution() -> None:
    fixtures = load_spiritual_spell_fixtures()

    with pytest.raises(CampaignPlanningError, match="no approved benchmark fixtures"):
        build_benchmark_campaign_draft(
            fixtures,
            objective="run reviewed Spiritual Spell benchmark fixtures",
            target_id="local-dev",
        )


def test_approved_local_fixture_can_plan_static_replay() -> None:
    fixture = _approved_fixture()

    draft = build_benchmark_campaign_draft(
        [fixture],
        objective="run reviewed Spiritual Spell benchmark fixtures",
        target_id="local-dev",
        target_system_prompt="You are a test assistant.",
    )

    assert draft.plan.risk_ids == [fixture.risk_plugin_id]
    assert draft.plan.strategy_ids == ["static_seed_replay"]
    assert draft.plan.scope.target_ids == ["local-dev"]
    assert draft.benchmark_metadata[0]["benchmark_fixture_id"] == fixture.id
    assert draft.blocked_fixture_ids == []


def test_plan_keeps_blocked_metadata_only_fixture_ids() -> None:
    approved = _approved_fixture()
    blocked = load_spiritual_spell_fixtures()[1]

    draft = build_benchmark_campaign_draft(
        [approved, blocked],
        objective="run reviewed Spiritual Spell benchmark fixtures",
        target_id="local-dev",
    )

    assert [fixture.id for fixture in draft.fixtures] == [approved.id]
    assert draft.blocked_fixture_ids == [blocked.id]


def test_live_target_requires_explicit_authorization() -> None:
    fixture = _approved_fixture()

    with pytest.raises(CampaignPlanningError, match="live target is authorized"):
        build_benchmark_campaign_draft(
            [fixture],
            objective="run reviewed Spiritual Spell benchmark fixtures",
            target_id="production-chatbot",
        )


def test_explicitly_authorized_live_target_is_scoped() -> None:
    fixture = _approved_fixture()

    draft = build_benchmark_campaign_draft(
        [fixture],
        objective="run reviewed Spiritual Spell benchmark fixtures",
        target_id="staging-chatbot",
        allow_live_target=True,
    )

    assert draft.plan.scope.target_ids == ["staging-chatbot"]


def test_unknown_risk_plugin_is_rejected_by_planner() -> None:
    fixture = _approved_fixture().model_copy(update={"risk_plugin_id": "unknown_risk"})

    with pytest.raises(CampaignPlanningError, match="unknown risk plugin"):
        build_benchmark_campaign_draft(
            [fixture],
            objective="run reviewed Spiritual Spell benchmark fixtures",
            target_id="local-dev",
        )


def test_summary_lines_include_fixture_and_blocked_counts() -> None:
    approved = _approved_fixture()
    blocked = load_spiritual_spell_fixtures()[1]

    draft = build_benchmark_campaign_draft(
        [approved, blocked],
        objective="run reviewed Spiritual Spell benchmark fixtures",
        target_id="local-dev",
    )

    lines = draft.summary_lines()

    assert "Executable fixtures: 1" in lines
    assert "Blocked fixtures: 1" in lines
    assert any(approved.id in line for line in lines)
