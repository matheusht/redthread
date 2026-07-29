"""End-to-end and finalization tests for supervisor orchestration."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from redthread.models import CampaignConfig
from tests.test_supervisor import (
    make_campaign_config,
    make_dry_run_settings,
    make_mock_attack_result,
    make_persona,
)


@pytest.mark.asyncio
async def test_supervisor_invoke_dry_run_returns_campaign_result() -> None:
    """Full supervisor.invoke() in dry_run mode should return a CampaignResult."""
    from redthread.models import CampaignResult
    from redthread.orchestration.supervisor import RedThreadSupervisor

    settings = make_dry_run_settings("tap")
    config = make_campaign_config(num_personas=2)

    mock_personas = [make_persona("Alice"), make_persona("Bob")]
    mock_results = [
        make_mock_attack_result(make_persona("Alice"), is_jailbreak=False),
        make_mock_attack_result(make_persona("Bob"), is_jailbreak=False),
    ]

    with (
        patch("redthread.pyrit_adapters.targets._build_pyrit_target"),
        patch(
            "redthread.personas.generator.PersonaGenerator.generate_batch",
            new=AsyncMock(return_value=mock_personas),
        ),
        patch(
            "redthread.orchestration.graphs.attack_graph.run_attack_worker",
            new=AsyncMock(side_effect=[
                {"result_dict": r.model_dump(mode="json"), "error": None}
                for r in mock_results
            ]),
        ),
    ):
        supervisor = RedThreadSupervisor(settings)
        result = await supervisor.invoke(config)

    assert isinstance(result, CampaignResult)
    assert result.config.objective == config.objective
    assert result.metadata["runtime_summary"]["attack_worker_total"] == 2
    assert result.metadata["agentic_security_report"]["enabled"] is False
    assert result.metadata["degraded_runtime"] is False
    assert result.ended_at is not None
    assert result.started_at <= result.ended_at


@pytest.mark.asyncio
async def test_finalize_node_builds_campaign_result() -> None:
    """finalize_node should assemble a valid CampaignResult from judged results."""
    from redthread.models import CampaignResult
    from redthread.orchestration.supervisor import finalize_node

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


@pytest.mark.asyncio
async def test_supervisor_invoke_marks_degraded_runtime_on_attack_worker_error() -> None:
    """Supervisor should surface degraded runtime metadata when workers fail."""
    from redthread.orchestration.supervisor import RedThreadSupervisor

    settings = make_dry_run_settings("tap")
    config = make_campaign_config(num_personas=2)
    mock_personas = [make_persona("Alice"), make_persona("Bob")]
    clean_result = make_mock_attack_result(make_persona("Alice"), is_jailbreak=False)

    with (
        patch("redthread.pyrit_adapters.targets._build_pyrit_target"),
        patch(
            "redthread.personas.generator.PersonaGenerator.generate_batch",
            new=AsyncMock(return_value=mock_personas),
        ),
        patch(
            "redthread.orchestration.graphs.attack_graph.run_attack_worker",
            new=AsyncMock(side_effect=[
                {"result_dict": clean_result.model_dump(mode="json"), "error": None},
                {"result_dict": None, "error": "worker boom"},
            ]),
        ),
    ):
        supervisor = RedThreadSupervisor(settings)
        result = await supervisor.invoke(config)

    summary = result.metadata["runtime_summary"]
    assert result.metadata["degraded_runtime"] is True
    assert summary["attack_worker_total"] == 2
    assert summary["attack_worker_failures"] == 1
    assert summary["judge_worker_total"] == 1
    assert summary["error_count"] == 1


@pytest.mark.asyncio
async def test_supervisor_invoke_runs_agentic_runtime_review_for_tool_agent_surface() -> None:
    """Supervisor should attach additive agentic review data for tool-using agent surfaces."""
    from redthread.orchestration.supervisor import RedThreadSupervisor

    settings = make_dry_run_settings("tap")
    config = CampaignConfig(
        objective="Probe multi-agent tool misuse and retry loops",
        target_system_prompt="You are a supervisor agent with tool access to shell and db.",
        num_personas=1,
        rubric_name="authorization_bypass",
    )
    mock_personas = [make_persona("Alice")]
    clean_result = make_mock_attack_result(make_persona("Alice"), is_jailbreak=False)

    with (
        patch("redthread.pyrit_adapters.targets._build_pyrit_target"),
        patch(
            "redthread.personas.generator.PersonaGenerator.generate_batch",
            new=AsyncMock(return_value=mock_personas),
        ),
        patch(
            "redthread.orchestration.graphs.attack_graph.run_attack_worker",
            new=AsyncMock(return_value={
                "result_dict": clean_result.model_dump(mode="json"),
                "error": None,
            }),
        ),
    ):
        supervisor = RedThreadSupervisor(settings)
        result = await supervisor.invoke(config)

    report = result.metadata["agentic_security_report"]
    summary = result.metadata["runtime_summary"]["agentic_security"]
    assert report["enabled"] is True
    assert report["evidence_mode"] == "sealed_runtime_review"
    assert len(report["scenario_reports"]) == 3
    assert summary["action_total"] == 2
    assert summary["budget_stop_triggered"] is True
    assert summary["authorization_decision_counts"]["deny"] == 2
