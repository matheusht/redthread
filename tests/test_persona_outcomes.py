from __future__ import annotations

from typing import Any

import pytest

from redthread.models import (
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
from redthread.personas.outcomes import (
    PersonaOutcomeTelemetry,
    build_persona_outcome_telemetry,
    persona_profiles_by_id,
)
from redthread.personas.prompt_layers import prompting_layer_profile_from_tags


def _persona(name: str, strategies: list[str]) -> Persona:
    return Persona(
        name=name,
        tactic=MitreAtlasTactic.INITIAL_ACCESS,
        technique="AML.T0054 — LLM Prompt Injection",
        cover_story="Routine authorization test",
        hidden_objective="Probe trusted instruction handling",
        system_prompt=f"You are {name}.",
        psychological_triggers=[PsychologicalTrigger.AUTHORITY],
        allowed_strategies=strategies,
    )


def _result(
    persona: Persona,
    *,
    outcome: AttackOutcome,
    score: float,
    is_jailbreak: bool = False,
) -> AttackResult:
    trace = AttackTrace(
        persona=persona,
        algorithm="mcts",
        turns=[
            ConversationTurn(
                turn_number=1,
                attacker_prompt="test prompt",
                target_response="test response",
            )
        ],
        outcome=outcome,
    )
    verdict = JudgeVerdict(
        score=score,
        raw_score=int(score),
        reasoning="JudgeAgent-owned verdict reasoning",
        feedback="feedback",
        rubric_name="authorization_bypass",
        is_jailbreak=is_jailbreak,
    )
    return AttackResult(
        trace=trace,
        verdict=verdict,
        iterations_used=2,
        duration_seconds=0.25,
    )


def test_persona_outcome_telemetry_tracks_weak_outcomes_and_coverage() -> None:
    profile = prompting_layer_profile_from_tags(
        technique_tags=["plain_language", "strategic_distraction"],
    )
    personas = [
        _persona("Plain", ["state the benign request plainly before adding context"]),
        _persona("Distract", ["use a secondary task frame while preserving the test objective"]),
    ]
    results = [
        _result(personas[0], outcome=AttackOutcome.FAILURE, score=3.2),
        _result(personas[1], outcome=AttackOutcome.SUCCESS, score=5.0, is_jailbreak=True),
    ]

    telemetry = build_persona_outcome_telemetry(
        results,
        persona_profiles_by_id(personas, profile),
    )

    assert telemetry.total_runs == 2
    assert telemetry.confirmed_jailbreaks == 1
    assert telemetry.near_misses == 1
    assert telemetry.enabled_layers == profile.enabled_layers
    assert telemetry.missing_layers == []
    assert telemetry.records[0].weak_outcome_label == "near_miss"
    assert telemetry.records[1].weak_outcome_label == "confirmed_jailbreak"
    assert "JudgeAgent" in " ".join(telemetry.notes)


def test_persona_outcome_telemetry_rejects_raw_prompt_loaded() -> None:
    with pytest.raises(ValueError, match="must not load raw prompt bodies"):
        PersonaOutcomeTelemetry(raw_prompt_loaded=True)


@pytest.mark.asyncio
async def test_finalize_attaches_persona_outcome_telemetry_metadata() -> None:
    from redthread.orchestration.supervisor import finalize_node

    profile = prompting_layer_profile_from_tags(technique_tags=["plain_language"])
    persona = _persona("Plain", ["state the benign request plainly before adding context"])
    result = _result(persona, outcome=AttackOutcome.SKIPPED, score=1.0)
    config = CampaignConfig(
        objective="Test trusted instruction handling",
        target_system_prompt="You are a guarded assistant.",
        num_personas=1,
        prompting_layer_profile=profile.model_dump(mode="json"),
    )
    state: dict[str, Any] = {
        "settings_dict": {},
        "config_dict": config.model_dump(mode="json"),
        "persona_dicts": [persona.model_dump(mode="json")],
        "attack_results": [],
        "attack_worker_total": 1,
        "attack_worker_failures": 0,
        "judged_results": [result.model_dump(mode="json")],
        "judge_worker_total": 1,
        "judge_worker_failures": 0,
        "defense_records": [],
        "defense_worker_total": 0,
        "defense_worker_failures": 0,
        "defense_deployments": 0,
        "agentic_security_report": {},
        "agentic_action_total": 0,
        "authorization_decision_counts": {},
        "canary_event_total": 0,
        "canary_report": {},
        "amplification_metrics": {},
        "budget_stop_triggered": False,
        "untrusted_lineage_action_total": 0,
        "campaign_result_dict": None,
        "errors": [],
    }

    output = await finalize_node(state)  # type: ignore[arg-type]

    metadata = output["campaign_result_dict"]["metadata"]
    telemetry = metadata["persona_outcome_telemetry"]
    assert telemetry["schema_version"] == "redthread.persona_outcome_telemetry.v1"
    assert telemetry["records"][0]["persona_id"] == persona.id
    assert telemetry["records"][0]["weak_outcome_label"] == "skipped"
    assert telemetry["records"][0]["covered_layers"] == ["plain_language"]
