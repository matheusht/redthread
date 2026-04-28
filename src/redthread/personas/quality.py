"""Persona strategy coverage checks and safe repair helpers."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from redthread.models import Persona
from redthread.personas.prompt_layers import PromptingLayerProfile, profile_strategy_hints

PERSONA_STRATEGY_COVERAGE_SCHEMA_VERSION: Literal[
    "redthread.persona_strategy_coverage.v1"
] = "redthread.persona_strategy_coverage.v1"


class PersonaStrategyCoverage(BaseModel):
    """Weak quality signal for persona strategy coverage.

    This is generation-quality metadata only. It is not a JudgeAgent verdict and
    must not become a finding or regression case.
    """

    schema_version: Literal["redthread.persona_strategy_coverage.v1"] = (
        PERSONA_STRATEGY_COVERAGE_SCHEMA_VERSION
    )
    persona_id: str
    persona_name: str
    enabled_layers: list[str] = Field(default_factory=list)
    covered_layers: list[str] = Field(default_factory=list)
    missing_layers: list[str] = Field(default_factory=list)
    strategy_count: int = 0
    raw_prompt_loaded: bool = False
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def reject_raw_prompt_loaded(self) -> PersonaStrategyCoverage:
        """Keep quality summaries safe for source control and reports."""
        if self.raw_prompt_loaded:
            msg = "persona strategy coverage must not load raw prompt bodies"
            raise ValueError(msg)
        return self

    @property
    def coverage_ratio(self) -> float:
        """Return covered enabled layers divided by enabled layers."""
        if not self.enabled_layers:
            return 1.0
        return len(self.covered_layers) / len(self.enabled_layers)


class PersonaBatchStrategyCoverage(BaseModel):
    """Weak batch-level quality signal for generated personas."""

    schema_version: Literal["redthread.persona_batch_strategy_coverage.v1"] = (
        "redthread.persona_batch_strategy_coverage.v1"
    )
    summaries: list[PersonaStrategyCoverage] = Field(default_factory=list)
    enabled_layers: list[str] = Field(default_factory=list)
    covered_layers: list[str] = Field(default_factory=list)
    missing_layers: list[str] = Field(default_factory=list)
    raw_prompt_loaded: bool = False

    @model_validator(mode="after")
    def reject_raw_prompt_loaded(self) -> PersonaBatchStrategyCoverage:
        """Keep batch summaries metadata-only."""
        if self.raw_prompt_loaded:
            msg = "persona batch strategy coverage must not load raw prompt bodies"
            raise ValueError(msg)
        return self



def assess_persona_strategy_coverage(
    persona: Persona,
    profile: PromptingLayerProfile | None,
) -> PersonaStrategyCoverage:
    """Measure whether a persona has safe strategies for each enabled layer."""
    if profile is None or profile.is_empty:
        return PersonaStrategyCoverage(
            persona_id=persona.id,
            persona_name=persona.name,
            strategy_count=len(persona.allowed_strategies),
            notes=["no prompting layer profile enabled"],
        )

    layer_hints = _layer_hint_map(profile)
    strategy_text = "\n".join(persona.allowed_strategies).lower()
    covered = [layer for layer, hint in layer_hints.items() if hint.lower() in strategy_text]
    missing = [layer for layer in layer_hints if layer not in covered]
    return PersonaStrategyCoverage(
        persona_id=persona.id,
        persona_name=persona.name,
        enabled_layers=list(layer_hints),
        covered_layers=covered,
        missing_layers=missing,
        strategy_count=len(persona.allowed_strategies),
        notes=["coverage is a weak generation-quality signal, not a verdict"],
    )


def assess_persona_batch_strategy_coverage(
    personas: list[Persona],
    profiles: list[PromptingLayerProfile | None],
) -> PersonaBatchStrategyCoverage:
    """Measure strategy coverage across a persona batch."""
    summaries = [
        assess_persona_strategy_coverage(
            persona,
            profiles[index] if index < len(profiles) else None,
        )
        for index, persona in enumerate(personas)
    ]
    enabled = _dedupe(layer for summary in summaries for layer in summary.enabled_layers)
    covered = _dedupe(layer for summary in summaries for layer in summary.covered_layers)
    missing = [layer for layer in enabled if layer not in covered]
    return PersonaBatchStrategyCoverage(
        summaries=summaries,
        enabled_layers=enabled,
        covered_layers=covered,
        missing_layers=missing,
    )


def repair_persona_strategy_coverage(
    persona: Persona,
    profile: PromptingLayerProfile | None,
) -> Persona:
    """Append safe fallback hints for enabled layers the model missed."""
    coverage = assess_persona_strategy_coverage(persona, profile)
    if not coverage.missing_layers or profile is None:
        return persona

    layer_hints = _layer_hint_map(profile)
    strategies = list(persona.allowed_strategies)
    seen = {strategy.lower() for strategy in strategies}
    for layer in coverage.missing_layers:
        hint = layer_hints[layer]
        if hint.lower() not in seen:
            strategies.append(hint)
            seen.add(hint.lower())
    return persona.model_copy(update={"allowed_strategies": strategies})


def _layer_hint_map(profile: PromptingLayerProfile) -> dict[str, str]:
    return dict(zip(profile.enabled_layers, profile_strategy_hints(profile), strict=True))


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
