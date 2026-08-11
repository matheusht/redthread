"""Worker and fan-out tests for supervisor orchestration."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from redthread.models import AttackOutcome
from tests.test_supervisor import (
    make_campaign_config,
    make_dry_run_settings,
    make_live_settings,
    make_mock_attack_result,
    make_persona,
)


@pytest.mark.asyncio
async def test_supervisor_fan_out_creates_one_worker_per_persona() -> None:
    """Verify fan_out_attack_workers creates one Send per persona."""
    from redthread.orchestration.supervisor import fan_out_attack_workers

    settings = make_dry_run_settings()
    personas = [make_persona("Alice"), make_persona("Bob"), make_persona("Carol")]

    state = {
        "settings_dict": settings.model_dump(mode="json"),
        "config_dict": make_campaign_config().model_dump(mode="json"),
        "persona_dicts": [p.model_dump(mode="json") for p in personas],
        "attack_results": [],
        "attack_worker_total": 0,
        "attack_worker_failures": 0,
        "judged_results": [],
        "judge_worker_total": 0,
        "judge_worker_failures": 0,
        "defense_records": [],
        "defense_worker_total": 0,
        "defense_worker_failures": 0,
        "defense_validated_candidates": 0,
        "defense_deployments": 0,
        "campaign_result_dict": None,
        "errors": [],
    }

    sends = fan_out_attack_workers(state)
    assert len(sends) == len(personas), "Must create one Send per persona"


@pytest.mark.asyncio
async def test_attack_worker_dry_run_returns_result() -> None:
    """Attack worker in dry_run mode should return a result without real LLM calls."""
    from redthread.orchestration.graphs.attack_graph import run_attack_worker

    settings = make_dry_run_settings("tap")
    persona = make_persona()

    with patch("redthread.pyrit_adapters.targets._build_pyrit_target"):
        output = await run_attack_worker({
            "settings_dict": settings.model_dump(mode="json"),
            "persona_dict": persona.model_dump(mode="json"),
            "target_system_prompt": "You are a guarded support assistant.",
            "rubric_name": "authorization_bypass",
            "result_dict": None,
            "error": None,
        })

    assert output["error"] is None, f"Worker errored: {output['error']}"
    assert output["result_dict"] is not None, "result_dict must be populated"
    assert output["result_dict"]["trace"]["outcome"] == AttackOutcome.SKIPPED.value
    assert (
        output["result_dict"]["trace"]["metadata"]["target_system_prompt"]
        == "You are a guarded support assistant."
    )


@pytest.mark.asyncio
async def test_judge_worker_dry_run_passes_through() -> None:
    """JudgeWorker in dry_run mode should pass the result through unchanged."""
    from redthread.orchestration.graphs.judge_graph import run_judge_worker

    settings = make_dry_run_settings()
    persona = make_persona()
    result = make_mock_attack_result(persona, is_jailbreak=False, score=2.0)

    output = await run_judge_worker({
        "settings_dict": settings.model_dump(mode="json"),
        "result_dict": result.model_dump(mode="json"),
        "rubric_name": "authorization_bypass",
        "judged_result_dict": None,
        "is_jailbreak": False,
        "final_score": 0.0,
        "error": None,
    })

    assert output["error"] is None
    assert output["judged_result_dict"] is not None
    assert output["is_jailbreak"] == result.verdict.is_jailbreak
    assert output["final_score"] == result.verdict.score
    assert (
        output["judged_result_dict"]["trace"]["metadata"]["judge_runtime_status"]
        == "sealed_passthrough"
    )


@pytest.mark.asyncio
async def test_judge_worker_marks_live_judge_failure_passthrough() -> None:
    """JudgeWorker should mark live judge failures as passthrough, not clean live proof."""
    from redthread.orchestration.graphs.judge_graph import run_judge_worker

    settings = make_live_settings()
    result = make_mock_attack_result(make_persona(), is_jailbreak=False, score=2.0)

    with patch(
        "redthread.evaluation.judge.JudgeAgent.evaluate",
        new=AsyncMock(side_effect=RuntimeError("judge boom")),
    ):
        output = await run_judge_worker({
            "settings_dict": settings.model_dump(mode="json"),
            "result_dict": result.model_dump(mode="json"),
            "rubric_name": "authorization_bypass",
            "judged_result_dict": None,
            "is_jailbreak": False,
            "final_score": 0.0,
            "error": None,
        })

    assert output["error"] == "judge boom"
    assert output["judged_result_dict"] is not None
    assert (
        output["judged_result_dict"]["trace"]["metadata"]["judge_runtime_status"]
        == "live_judge_error_passthrough"
    )
    assert output["judged_result_dict"]["trace"]["metadata"]["judge_error"] == "judge boom"
