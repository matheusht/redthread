"""Tests for LangGraph supervisor routing and campaign finalization."""

from __future__ import annotations

import pytest

from redthread.models import CampaignResult
from redthread.orchestration.supervisor import finalize_node, route_to_defense
from tests.test_supervisor_fixtures import (
    make_campaign_config,
    make_dry_run_settings,
    make_mock_attack_result,
    make_persona,
)


def test_route_to_defense_routes_jailbreak() -> None:
    """route_to_defense should return 'defense_synthesis' when jailbreaks exist."""
    jailbreak_result = make_mock_attack_result(make_persona(), is_jailbreak=True, score=5.0)

    state = {
        "settings_dict": {},
        "config_dict": {},
        "persona_dicts": [],
        "attack_results": [],
        "attack_worker_total": 0,
        "attack_worker_failures": 0,
        "judged_results": [jailbreak_result.model_dump(mode="json")],
        "judge_worker_total": 1,
        "judge_worker_failures": 0,
        "defense_records": [],
        "defense_worker_total": 0,
        "defense_worker_failures": 0,
        "defense_validated_candidates": 0,
        "defense_deployments": 0,
        "campaign_result_dict": None,
        "errors": [],
    }

    route = route_to_defense(state)
    assert route == "defense_synthesis"


def test_route_to_defense_skips_on_clean_results() -> None:
    """route_to_defense should return 'finalize' when no jailbreaks exist."""
    clean_result = make_mock_attack_result(make_persona(), is_jailbreak=False, score=1.5)

    state = {
        "settings_dict": {},
        "config_dict": {},
        "persona_dicts": [],
        "attack_results": [],
        "attack_worker_total": 0,
        "attack_worker_failures": 0,
        "judged_results": [clean_result.model_dump(mode="json")],
        "judge_worker_total": 1,
        "judge_worker_failures": 0,
        "defense_records": [],
        "defense_worker_total": 0,
        "defense_worker_failures": 0,
        "defense_validated_candidates": 0,
        "defense_deployments": 0,
        "campaign_result_dict": None,
        "errors": [],
    }

    route = route_to_defense(state)
    assert route == "finalize"


@pytest.mark.asyncio
async def test_finalize_node_builds_campaign_result() -> None:
    """finalize_node should assemble a valid CampaignResult from judged results."""
    persona = make_persona()
    result1 = make_mock_attack_result(persona, is_jailbreak=False, score=2.0)
    result2 = make_mock_attack_result(persona, is_jailbreak=False, score=1.5)

    settings = make_dry_run_settings()
    config = make_campaign_config()

    state = {
        "settings_dict": settings.model_dump(mode="json"),
        "config_dict": config.model_dump(mode="json"),
        "persona_dicts": [],
        "attack_results": [],
        "attack_worker_total": 2,
        "attack_worker_failures": 0,
        "judged_results": [
            result1.model_dump(mode="json"),
            result2.model_dump(mode="json"),
        ],
        "judge_worker_total": 2,
        "judge_worker_failures": 0,
        "defense_records": [],
        "defense_worker_total": 0,
        "defense_worker_failures": 0,
        "defense_validated_candidates": 0,
        "defense_deployments": 0,
        "campaign_result_dict": None,
        "errors": [],
    }

    output = await finalize_node(state)
    assert "campaign_result_dict" in output

    campaign = CampaignResult.model_validate(output["campaign_result_dict"])
    assert len(campaign.results) == 2
    assert campaign.attack_success_rate == 0.0
    assert campaign.metadata["degraded_runtime"] is False
    assert campaign.metadata["runtime_summary"]["judge_worker_total"] == 2
