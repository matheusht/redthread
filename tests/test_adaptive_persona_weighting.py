from __future__ import annotations

from typing import Any, cast

import pytest

from redthread.config.settings import RedThreadSettings
from redthread.core.regression_cases import RegressionCaseError, regression_case_from_attack_result
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
from redthread.personas.adaptive_weighting import (
    AdaptivePersonaWeightingPlan,
    build_adaptive_persona_weighting_plan,
)
from redthread.personas.batch_planning import prompting_layer_profiles_for_batch
from redthread.personas.generator import PersonaGenerator
from redthread.personas.outcomes import (
    PersonaOutcomeTelemetry,
    build_persona_outcome_telemetry,
    persona_profiles_by_id,
)
from redthread.personas.prompt_layers import (
    PromptingLayerProfile,
    prompting_layer_profile_from_tags,
)


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
    return AttackResult(
        trace=trace,
        verdict=JudgeVerdict(
            score=score,
            raw_score=int(score),
            reasoning="JudgeAgent-owned verdict reasoning",
            feedback="feedback",
            rubric_name="authorization_bypass",
            is_jailbreak=is_jailbreak,
        ),
        iterations_used=1,
        duration_seconds=0.1,
    )


def _telemetry_fixture() -> tuple[PromptingLayerProfile, PersonaOutcomeTelemetry, AttackResult]:
    profile = prompting_layer_profile_from_tags(
        technique_tags=["plain_language", "strategic_distraction", "narrative_embedding"],
    )
    personas = [
        _persona("Plain", ["state the benign request plainly before adding context"]),
        _persona("Distract", ["use a secondary task frame while preserving the test objective"]),
        _persona("Narrative", ["embed the request in a realistic multi-step scenario"]),
    ]
    results = [
        _result(personas[0], outcome=AttackOutcome.PARTIAL, score=3.2),
        _result(personas[1], outcome=AttackOutcome.SUCCESS, score=5.0, is_jailbreak=True),
        _result(personas[2], outcome=AttackOutcome.FAILURE, score=1.0),
    ]
    telemetry = build_persona_outcome_telemetry(
        results,
        persona_profiles_by_id(personas, profile),
    )
    return profile, telemetry, results[0]


def test_adaptive_weighting_plan_prefers_judge_confirmed_and_near_miss_layers() -> None:
    _, telemetry, _ = _telemetry_fixture()

    plan = build_adaptive_persona_weighting_plan(telemetry)
    weights = plan.weights_by_layer()

    assert plan.schema_version == "redthread.adaptive_persona_weighting_plan.v1"
    assert plan.ordered_layers[0] == "strategic_distraction"
    assert weights["strategic_distraction"] > weights["plain_language"]
    assert weights["plain_language"] > weights["narrative_embedding"]
    assert not any(weight.durable_regression_evidence for weight in plan.layer_weights)
    assert "JudgeAgent-confirmed" in plan.durable_regression_evidence_policy


def test_weighted_batch_planning_emphasizes_higher_weight_layers() -> None:
    profile, telemetry, _ = _telemetry_fixture()
    plan = build_adaptive_persona_weighting_plan(telemetry)

    profiles = prompting_layer_profiles_for_batch(profile, 4, plan.weights_by_layer())
    counts = {
        layer: sum(1 for item in profiles if item is not None and layer in item.enabled_layers)
        for layer in profile.enabled_layers
    }

    assert counts["strategic_distraction"] > counts["plain_language"]
    assert counts["plain_language"] > counts["narrative_embedding"]


@pytest.mark.asyncio
async def test_generate_batch_accepts_adaptive_persona_weighting_plan() -> None:
    profile, telemetry, _ = _telemetry_fixture()
    plan = build_adaptive_persona_weighting_plan(telemetry)
    generator = PersonaGenerator(RedThreadSettings(dry_run=True))

    personas = await generator.generate_batch(
        "test trusted instruction handling",
        count=4,
        prompting_layer_profile=profile,
        persona_weighting_plan=plan,
    )
    strategies = ["\n".join(persona.allowed_strategies) for persona in personas]

    assert sum("secondary task frame" in item for item in strategies) > sum(
        "realistic multi-step scenario" in item for item in strategies
    )


@pytest.mark.asyncio
async def test_supervisor_generation_accepts_adaptive_weighting_plan_from_config() -> None:
    from redthread.orchestration.supervisor import generate_personas_node

    profile, telemetry, _ = _telemetry_fixture()
    plan = build_adaptive_persona_weighting_plan(telemetry)
    config = CampaignConfig(
        objective="test trusted instruction handling",
        target_system_prompt="You are a guarded assistant.",
        num_personas=4,
        prompting_layer_profile=profile.model_dump(mode="json"),
        persona_weighting_plan=plan.model_dump(mode="json"),
    )
    settings = RedThreadSettings(dry_run=True)

    state = {
        "settings_dict": settings.model_dump(mode="json"),
        "config_dict": config.model_dump(mode="json"),
    }
    output = await generate_personas_node(cast(Any, state))
    strategy_texts = ["\n".join(item["allowed_strategies"]) for item in output["persona_dicts"]]

    assert sum("secondary task frame" in item for item in strategy_texts) > sum(
        "realistic multi-step scenario" in item for item in strategy_texts
    )


def test_adaptive_weighting_rejects_raw_prompt_loaded() -> None:
    with pytest.raises(ValueError, match="must not load raw prompt bodies"):
        AdaptivePersonaWeightingPlan(
            source_telemetry_schema_version="redthread.persona_outcome_telemetry.v1",
            raw_prompt_loaded=True,
        )


def test_near_miss_weighting_does_not_create_regression_case() -> None:
    _, _, near_miss = _telemetry_fixture()

    with pytest.raises(RegressionCaseError, match="confirmed JudgeAgent finding"):
        regression_case_from_attack_result(near_miss)
