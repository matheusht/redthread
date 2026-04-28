from __future__ import annotations

import json
from typing import Any

import pytest

from redthread.config.settings import RedThreadSettings
from redthread.models import MitreAtlasTactic, Persona, PsychologicalTrigger
from redthread.personas.batch_planning import prompting_layer_profiles_for_batch
from redthread.personas.generator import PersonaGenerator
from redthread.personas.prompt_layers import prompting_layer_profile_from_tags
from redthread.personas.quality import (
    assess_persona_batch_strategy_coverage,
    assess_persona_strategy_coverage,
    repair_persona_strategy_coverage,
)


def _persona(strategies: list[str]) -> Persona:
    return Persona(
        name="Quality Tester",
        tactic=MitreAtlasTactic.INITIAL_ACCESS,
        technique="AML.T0054 — LLM Prompt Injection",
        cover_story="Routine authorization test",
        hidden_objective="Probe trusted instruction handling",
        system_prompt="You are Quality Tester.",
        psychological_triggers=[PsychologicalTrigger.AUTHORITY],
        allowed_strategies=strategies,
    )


def test_persona_strategy_quality_finds_missing_layers() -> None:
    profile = prompting_layer_profile_from_tags(
        technique_tags=["plain_language", "narrative_embedding"],
    )
    persona = _persona(["state the benign request plainly before adding context"])

    summary = assess_persona_strategy_coverage(persona, profile)

    assert summary.covered_layers == ["plain_language"]
    assert summary.missing_layers == ["narrative_embedding"]
    assert summary.coverage_ratio == 0.5
    assert summary.raw_prompt_loaded is False


def test_repair_persona_strategy_coverage_appends_safe_missing_hints() -> None:
    profile = prompting_layer_profile_from_tags(
        technique_tags=["plain_language", "strategic_distraction"],
    )
    persona = _persona(["state the benign request plainly before adding context"])

    repaired = repair_persona_strategy_coverage(persona, profile)

    assert repaired is not persona
    assert repaired.allowed_strategies == [
        "state the benign request plainly before adding context",
        "use a secondary task frame while preserving the test objective",
    ]


def test_batch_planning_distributes_enabled_layers_across_personas() -> None:
    profile = prompting_layer_profile_from_tags(
        technique_tags=[
            "plain_language",
            "strategic_distraction",
            "narrative_embedding",
            "reasoning_hijack_attempt",
        ],
        persona_tags=["eni_writer"],
    )

    profiles = prompting_layer_profiles_for_batch(profile, 3)

    assert len(profiles) == 3
    enabled = {layer for item in profiles if item for layer in item.enabled_layers}
    assert enabled == set(profile.enabled_layers)
    assert all(item is not None and item.enabled_layers for item in profiles)


@pytest.mark.asyncio
async def test_generate_batch_uses_distributed_prompting_layer_profiles() -> None:
    generator = PersonaGenerator(RedThreadSettings(dry_run=True))
    profile = prompting_layer_profile_from_tags(
        technique_tags=["plain_language", "strategic_distraction", "narrative_embedding"],
    )

    personas = await generator.generate_batch(
        "test trusted instruction handling",
        count=3,
        prompting_layer_profile=profile,
    )
    profiles = prompting_layer_profiles_for_batch(profile, 3)
    batch_summary = assess_persona_batch_strategy_coverage(personas, profiles)

    assert batch_summary.missing_layers == []
    assert set(batch_summary.covered_layers) == set(profile.enabled_layers)


@pytest.mark.asyncio
async def test_live_generation_repairs_missing_profile_strategy_hints() -> None:
    class FakeTarget:
        async def send(self, **_: Any) -> str:
            return json.dumps(
                {
                    "name": "Live Tester",
                    "cover_story": "Routine authorization test",
                    "hidden_objective": "Probe trusted instruction handling",
                    "system_prompt": "You are Live Tester.",
                    "allowed_strategies": ["cite audit authority"],
                }
            )

    generator = PersonaGenerator(RedThreadSettings(dry_run=False))
    generator._attacker = FakeTarget()  # type: ignore[assignment]
    profile = prompting_layer_profile_from_tags(
        technique_tags=["plain_language", "strategic_distraction"],
    )

    persona = await generator.generate(
        "test trusted instruction handling",
        prompting_layer_profile=profile,
    )

    strategies = "\n".join(persona.allowed_strategies)
    assert "state the benign request plainly" in strategies
    assert "secondary task frame" in strategies
