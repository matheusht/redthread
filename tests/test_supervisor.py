"""Tests for the LangGraph Supervisor — Phase 4 orchestration.

Verifies:
  - LangGraph fan-out spawns one attack worker per persona
  - Results are properly collected and aggregated
  - Conditional routing sends jailbreaks to defense synthesis
  - Supervisor.invoke() returns a valid CampaignResult
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from redthread.config.settings import AlgorithmType, RedThreadSettings, TargetBackend
from redthread.models import (
    AttackNode,
    AttackOutcome,
    AttackResult,
    AttackTrace,
    CampaignConfig,
    ConversationTurn,
    JudgeVerdict,
    MitreAtlasTactic,
    Persona,
    PsychologicalTrigger,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_dry_run_settings(algorithm: str = "tap") -> RedThreadSettings:
    return RedThreadSettings(
        target_backend=TargetBackend.OLLAMA,
        target_model="llama3.2:3b",
        attacker_backend=TargetBackend.OLLAMA,
        attacker_model="llama3.2:3b",
        judge_backend=TargetBackend.OPENAI,
        judge_model="gpt-4o",
        openai_api_key="test-key",
        algorithm=AlgorithmType(algorithm),
        branching_factor=2,
        tree_depth=2,
        tree_width=3,
        dry_run=True,
    )


def make_campaign_config(num_personas: int = 2) -> CampaignConfig:
    return CampaignConfig(
        objective="Test authorization bypass",
        target_system_prompt="You are a helpful assistant.",
        num_personas=num_personas,
        rubric_name="authorization_bypass",
    )


def make_persona(name: str = "Test Persona") -> Persona:
    return Persona(
        name=name,
        tactic=MitreAtlasTactic.INITIAL_ACCESS,
        technique="AML.T0051",
        cover_story="Routine audit",
        hidden_objective="Bypass authorization checks",
        system_prompt="You are a persistent auditor...",
        psychological_triggers=[PsychologicalTrigger.AUTHORITY],
    )


def make_mock_attack_result(
    persona: Persona,
    is_jailbreak: bool = False,
    score: float = 1.5,
) -> AttackResult:
    trace = AttackTrace(
        persona=persona,
        algorithm="tap",
        turns=[
            ConversationTurn(
                turn_number=1,
                attacker_prompt="Test attack prompt",
                target_response="Target response",
            )
        ],
        outcome=AttackOutcome.SUCCESS if is_jailbreak else AttackOutcome.FAILURE,
    )
    verdict = JudgeVerdict(
        score=score,
        raw_score=int(score),
        reasoning="Test reasoning",
        feedback="Test feedback",
        rubric_name="authorization_bypass",
        is_jailbreak=is_jailbreak,
    )
    return AttackResult(trace=trace, verdict=verdict, iterations_used=3, duration_seconds=0.5)


# ── Test: fan-out attack workers ──────────────────────────────────────────────

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
        "judged_results": [],
        "defense_records": [],
        "campaign_result_dict": None,
        "errors": [],
    }

    sends = fan_out_attack_workers(state)
    assert len(sends) == len(personas), "Must create one Send per persona"


# ── Test: attack worker (dry run) ─────────────────────────────────────────────

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
            "rubric_name": "authorization_bypass",
            "result_dict": None,
            "error": None,
        })

    assert output["error"] is None, f"Worker errored: {output['error']}"
    assert output["result_dict"] is not None, "result_dict must be populated"
    # Dry run → outcome should be SKIPPED
    assert output["result_dict"]["trace"]["outcome"] == AttackOutcome.SKIPPED.value


# ── Test: judge worker (dry run) ──────────────────────────────────────────────

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


# ── Test: defense routing ─────────────────────────────────────────────────────

def test_route_to_defense_routes_jailbreak() -> None:
    """route_to_defense should return 'defense_synthesis' when jailbreaks exist."""
    from redthread.orchestration.supervisor import route_to_defense

    jailbreak_result = make_mock_attack_result(make_persona(), is_jailbreak=True, score=5.0)

    state = {
        "settings_dict": {},
        "config_dict": {},
        "persona_dicts": [],
        "attack_results": [],
        "judged_results": [jailbreak_result.model_dump(mode="json")],
        "defense_records": [],
        "campaign_result_dict": None,
        "errors": [],
    }

    route = route_to_defense(state)
    assert route == "defense_synthesis"


def test_route_to_defense_skips_on_clean_results() -> None:
    """route_to_defense should return 'finalize' when no jailbreaks exist."""
    from redthread.orchestration.supervisor import route_to_defense

    clean_result = make_mock_attack_result(make_persona(), is_jailbreak=False, score=1.5)

    state = {
        "settings_dict": {},
        "config_dict": {},
        "persona_dicts": [],
        "attack_results": [],
        "judged_results": [clean_result.model_dump(mode="json")],
        "defense_records": [],
        "campaign_result_dict": None,
        "errors": [],
    }

    route = route_to_defense(state)
    assert route == "finalize"


# ── Test: full supervisor.invoke() round-trip ─────────────────────────────────

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


# ── Test: state transition — finalize node ────────────────────────────────────

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
        "judged_results": [
            result1.model_dump(mode="json"),
            result2.model_dump(mode="json"),
        ],
        "defense_records": [],
        "campaign_result_dict": None,
        "errors": [],
    }

    output = await finalize_node(state)
    assert "campaign_result_dict" in output

    campaign = CampaignResult.model_validate(output["campaign_result_dict"])
    assert len(campaign.results) == 2
    assert campaign.attack_success_rate == 0.0  # No jailbreaks in test data
