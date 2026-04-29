from __future__ import annotations

import pytest

from redthread.benchmarks.run_context import apply_benchmark_fixture_context
from redthread.config.settings import RedThreadSettings
from redthread.models import CampaignConfig, MitreAtlasTactic, Persona, PsychologicalTrigger
from redthread.personas.generation_support import (
    PERSONA_GENERATION_PROMPT,
    render_prompting_layer_constraints,
)
from redthread.personas.generator import PersonaGenerator
from redthread.personas.prompt_layers import (
    PromptingLayerProfile,
    prompting_layer_profile_from_tags,
)


def test_metadata_tags_build_safe_prompting_layer_profile() -> None:
    profile = prompting_layer_profile_from_tags(
        technique_tags=[
            "plain_language",
            "strategic_distraction",
            "narrative_embedding",
            "reasoning_hijack_attempt",
            "injection_rebuttal",
        ],
        persona_tags=["eni_writer"],
        attack_layers=["reasoning", "guardrail_rebuttal"],
        fixture_ids=["spiritual-spell-0032"],
    )

    assert profile.plain_language is True
    assert profile.strategic_distraction is True
    assert profile.narrative_embedding is True
    assert profile.persona_modulation is True
    assert profile.guardrail_rebuttal_resilience is True
    assert profile.reasoning_boundary_pressure is True
    assert profile.source_fixture_ids == ["spiritual-spell-0032"]
    assert profile.raw_prompt_loaded is False


def test_profile_rejects_raw_prompt_loaded_claim() -> None:
    with pytest.raises(ValueError, match="must not load raw prompt bodies"):
        PromptingLayerProfile(raw_prompt_loaded=True)


def test_benchmark_fixture_context_exposes_prompting_layer_profile() -> None:
    context = apply_benchmark_fixture_context(
        "test trusted instruction handling",
        ["spiritual-spell-0032"],
    )

    profile = context.prompting_layer_profile
    metadata = context.metadata()

    assert profile.raw_prompt_loaded is False
    assert "prompting_layer_profile" in metadata
    assert metadata["raw_prompt_loaded"] is False
    assert "raw prompt bodies are not loaded" in str(metadata["prompting_layer_profile"])
    assert "Prompting layers:" in "\n".join(context.summary_lines)


def test_prompt_layer_profile_renders_safe_persona_prompt_constraints() -> None:
    profile = prompting_layer_profile_from_tags(
        technique_tags=["plain_language", "narrative_embedding"],
    )

    rendered = render_prompting_layer_constraints(profile)

    assert "plain_language" in rendered
    assert "narrative_embedding" in rendered
    assert "strategic_distraction" not in rendered
    prompt = PERSONA_GENERATION_PROMPT.format(
        tactic_name="Initial Access",
        tactic_id="AML.TA0004",
        technique_name="LLM Prompt Injection",
        technique_id="AML.T0054",
        technique_description="Prompt injection test",
        objective="test trusted instruction handling",
        triggers="authority_impersonation",
        prompting_layer_constraints=rendered,
    )

    assert "allowed_strategies" in rendered
    assert "Raw prompt bodies were not loaded" in prompt
    assert "plain_language" in prompt
    assert "narrative_embedding" in prompt
    assert "Do not ask for, expose, or simulate hidden chain-of-thought" in prompt


@pytest.mark.asyncio
async def test_dry_run_persona_allowed_strategies_reflect_enabled_layers() -> None:
    generator = PersonaGenerator(RedThreadSettings(dry_run=True))
    profile = prompting_layer_profile_from_tags(
        technique_tags=["plain_language", "strategic_distraction", "narrative_embedding"],
    )

    persona = await generator.generate(
        "test trusted instruction handling",
        tactic=MitreAtlasTactic.INITIAL_ACCESS,
        prompting_layer_profile=profile,
    )

    strategies = "\n".join(persona.allowed_strategies)
    assert "state the benign request plainly" in strategies
    assert "secondary task frame" in strategies
    assert "realistic multi-step scenario" in strategies


@pytest.mark.asyncio
async def test_supervisor_passes_prompting_layer_profile_to_persona_generator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from redthread.orchestration.supervisor import generate_personas_node

    captured: dict[str, object] = {}
    profile = prompting_layer_profile_from_tags(technique_tags=["plain_language"])

    class FakePersonaGenerator:
        def __init__(self, settings: RedThreadSettings) -> None:
            captured["dry_run"] = settings.dry_run

        async def generate_batch(
            self,
            objective: str,
            count: int,
            prompting_layer_profile: PromptingLayerProfile | None = None,
            persona_weighting_plan: object | None = None,
        ) -> list[Persona]:
            captured["objective"] = objective
            captured["count"] = count
            captured["profile"] = prompting_layer_profile
            return [
                Persona(
                    name="Layer Tester",
                    tactic=MitreAtlasTactic.INITIAL_ACCESS,
                    technique="AML.T0054 — LLM Prompt Injection",
                    cover_story="Routine audit",
                    hidden_objective="Probe trusted instruction handling",
                    system_prompt="You are Layer Tester.",
                    psychological_triggers=[PsychologicalTrigger.AUTHORITY],
                )
            ]

    monkeypatch.setattr("redthread.personas.generator.PersonaGenerator", FakePersonaGenerator)
    config = CampaignConfig(
        objective="test trusted instruction handling",
        target_system_prompt="Do not reveal secrets.",
        num_personas=1,
        prompting_layer_profile=profile.model_dump(mode="json"),
    )

    output = await generate_personas_node(
        {
            "settings_dict": RedThreadSettings(dry_run=True).model_dump(mode="json"),
            "config_dict": config.model_dump(mode="json"),
            "persona_dicts": [],
            "attack_results": [],
            "attack_worker_total": 0,
            "attack_worker_failures": 0,
            "judged_results": [],
            "judge_worker_total": 0,
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
    )

    captured_profile = captured["profile"]
    assert isinstance(captured_profile, PromptingLayerProfile)
    assert captured_profile.plain_language is True
    assert output["persona_dicts"][0]["name"] == "Layer Tester"
