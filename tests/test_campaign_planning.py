"""Tests for Slice 2 campaign planning parser."""

from __future__ import annotations

import pytest

from redthread.models import CampaignConfig
from redthread.orchestration.campaign_planning import CampaignPlanningError, build_campaign_plan


def test_existing_campaign_config_builds_legacy_plan() -> None:
    config = CampaignConfig(
        objective="test for authorization bypass",
        target_system_prompt="You are a support agent.",
        rubric_name="authorization_bypass",
        num_personas=2,
    )

    plan = build_campaign_plan(config)

    assert plan.objective == "test for authorization bypass"
    assert plan.target_system_prompt == "You are a support agent."
    assert plan.risk_ids == ["legacy_objective"]
    assert plan.strategy_ids == ["static_seed_replay"]
    assert plan.risks[0].plugin.source == "redthread_legacy_campaign_config"


def test_new_config_resolves_builtin_risks_strategies_and_scope() -> None:
    plan = build_campaign_plan(
        {
            "objective": "support-agent security pass",
            "target_system_prompt": "You are a support agent.",
            "rubric_name": "sensitive_info",
            "num_personas": 4,
            "risks": ["prompt_injection", {"id": "sensitive_data_exfiltration"}],
            "strategies": {"include": ["crescendo", "static_seed_replay"], "max_cost": "medium"},
            "scope": {
                "target_ids": ["support-agent-dev"],
                "allowed_tools": ["target_llm"],
                "allowed_domains": ["dev.example.com"],
                "can_use_network": True,
            },
        }
    )

    assert plan.risk_ids == ["prompt_injection", "sensitive_data_exfiltration"]
    assert plan.strategy_ids == ["crescendo", "static_seed_replay"]
    assert plan.risks[0].strategy_ids == ["crescendo", "static_seed_replay"]
    assert plan.scope.allows_target("support-agent-dev") is True
    assert plan.scope.allows_tool("target_llm") is True
    assert plan.scope.allows_domain("api.dev.example.com") is True


def test_custom_policy_becomes_temporary_risk_plugin() -> None:
    plan = build_campaign_plan(
        {
            "objective": "custom business policy test",
            "target_system_prompt": "You are a sales assistant.",
            "risks": [
                {
                    "custom_policy": {
                        "id": "no_contractual_commitments",
                        "text": "The assistant must not make binding commitments.",
                        "name": "No contractual commitments",
                    }
                }
            ],
        }
    )

    plugin = plan.risks[0].plugin
    assert plugin.id == "no_contractual_commitments"
    assert plugin.name == "No contractual commitments"
    assert plugin.policy_text == "The assistant must not make binding commitments."
    assert plugin.source == "redthread_custom_policy"
    assert plan.risks[0].strategy_ids == ["static_seed_replay"]


def test_unknown_risk_fails_early() -> None:
    with pytest.raises(CampaignPlanningError, match="unknown risk plugin"):
        build_campaign_plan(
            {
                "objective": "bad risk",
                "target_system_prompt": "Prompt",
                "risks": ["missing_risk"],
            }
        )


def test_unknown_strategy_fails_early() -> None:
    with pytest.raises(CampaignPlanningError, match="unknown attack strategy"):
        build_campaign_plan(
            {
                "objective": "bad strategy",
                "target_system_prompt": "Prompt",
                "risks": ["prompt_injection"],
                "strategies": {"include": ["missing_strategy"]},
            }
        )


def test_incompatible_strategy_fails_early() -> None:
    with pytest.raises(CampaignPlanningError, match="no compatible strategies"):
        build_campaign_plan(
            {
                "objective": "bad compatibility",
                "target_system_prompt": "Prompt",
                "risks": ["prompt_injection"],
                "strategies": {"include": ["pair"]},
            }
        )


def test_max_cost_can_filter_out_selected_strategies_and_fail() -> None:
    with pytest.raises(CampaignPlanningError, match="no compatible strategies"):
        build_campaign_plan(
            {
                "objective": "cost capped",
                "target_system_prompt": "Prompt",
                "risks": ["prompt_injection"],
                "strategies": {"include": ["tap"], "max_cost": "medium"},
            }
        )


def test_summary_lines_are_deterministic_and_operator_readable() -> None:
    plan = build_campaign_plan(
        {
            "objective": "summary test",
            "target_system_prompt": "Prompt",
            "risks": ["prompt_injection"],
            "strategies": {"include": ["crescendo"]},
            "scope": {"target_ids": ["target-a"]},
        }
    )

    assert plan.summary_lines() == [
        "Objective: summary test",
        "Rubric: authorization_bypass",
        "Personas: 3",
        "Risks: prompt_injection",
        "Strategies: crescendo",
        "Scope targets: target-a",
        "- prompt_injection: crescendo",
    ]
