"""Adaptive persona layer weighting from weak outcome telemetry."""

from __future__ import annotations

from collections.abc import Mapping
from statistics import mean
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from redthread.personas.outcomes import PersonaOutcomeRecord, PersonaOutcomeTelemetry

ADAPTIVE_PERSONA_LAYER_WEIGHT_SCHEMA_VERSION: Literal[
    "redthread.adaptive_persona_layer_weight.v1"
] = "redthread.adaptive_persona_layer_weight.v1"
ADAPTIVE_PERSONA_WEIGHTING_PLAN_SCHEMA_VERSION: Literal[
    "redthread.adaptive_persona_weighting_plan.v1"
] = "redthread.adaptive_persona_weighting_plan.v1"


class AdaptivePersonaLayerWeight(BaseModel):
    """Planning-only layer weight derived from judged persona telemetry."""

    schema_version: Literal["redthread.adaptive_persona_layer_weight.v1"] = (
        ADAPTIVE_PERSONA_LAYER_WEIGHT_SCHEMA_VERSION
    )
    layer: str
    weight: float = Field(ge=0.25)
    observed_runs: int = 0
    judge_confirmed_jailbreaks: int = 0
    weak_near_misses: int = 0
    skipped: int = 0
    errors: int = 0
    average_judge_score: float = 0.0
    durable_regression_evidence: bool = False
    evidence_note: str = "weak persona telemetry only; JudgeAgent owns findings"


class AdaptivePersonaWeightingPlan(BaseModel):
    """Next-run persona weighting plan built from weak telemetry."""

    schema_version: Literal["redthread.adaptive_persona_weighting_plan.v1"] = (
        ADAPTIVE_PERSONA_WEIGHTING_PLAN_SCHEMA_VERSION
    )
    source_telemetry_schema_version: str
    layer_weights: list[AdaptivePersonaLayerWeight] = Field(default_factory=list)
    ordered_layers: list[str] = Field(default_factory=list)
    raw_prompt_loaded: bool = False
    durable_regression_evidence_policy: str = (
        "only JudgeAgent-confirmed AttackResult objects can become durable regression evidence"
    )
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def reject_raw_prompt_loaded(self) -> AdaptivePersonaWeightingPlan:
        """Keep adaptive plans metadata-only."""
        if self.raw_prompt_loaded:
            msg = "adaptive persona weighting must not load raw prompt bodies"
            raise ValueError(msg)
        return self

    def weights_by_layer(self) -> dict[str, float]:
        """Return layer weights as a mapping for batch planning."""
        return {item.layer: item.weight for item in self.layer_weights}


def build_adaptive_persona_weighting_plan(
    telemetry: PersonaOutcomeTelemetry | Mapping[str, object],
) -> AdaptivePersonaWeightingPlan:
    """Build a planning-only next-run layer weighting plan from weak telemetry."""
    parsed = (
        telemetry
        if isinstance(telemetry, PersonaOutcomeTelemetry)
        else PersonaOutcomeTelemetry.model_validate(telemetry)
    )
    weights = [_layer_weight(layer, parsed.records) for layer in parsed.enabled_layers]
    weights.sort(key=lambda item: (-item.weight, item.layer))
    return AdaptivePersonaWeightingPlan(
        source_telemetry_schema_version=parsed.schema_version,
        layer_weights=weights,
        ordered_layers=[item.layer for item in weights],
        raw_prompt_loaded=False,
        notes=[
            "adaptive persona weighting is a next-run planning hint, not evidence",
            "near misses may raise exploration weight but cannot create findings",
            "durable regression evidence still requires JudgeAgent-confirmed AttackResult objects",
        ],
    )


def _layer_weight(layer: str, records: list[PersonaOutcomeRecord]) -> AdaptivePersonaLayerWeight:
    observed = [record for record in records if layer in record.covered_layers]
    confirmed = sum(1 for record in observed if record.judge_verdict_is_jailbreak)
    near_misses = sum(1 for record in observed if record.weak_outcome_label == "near_miss")
    skipped = sum(1 for record in observed if record.weak_outcome_label == "skipped")
    errors = sum(1 for record in observed if record.weak_outcome_label == "error")
    average_score = mean([record.judge_score for record in observed]) if observed else 0.0
    weight = max(0.25, 1.0 + (confirmed * 2.0) + (near_misses * 0.75))
    return AdaptivePersonaLayerWeight(
        layer=layer,
        weight=round(weight, 2),
        observed_runs=len(observed),
        judge_confirmed_jailbreaks=confirmed,
        weak_near_misses=near_misses,
        skipped=skipped,
        errors=errors,
        average_judge_score=round(average_score, 3),
    )


__all__ = [
    "ADAPTIVE_PERSONA_LAYER_WEIGHT_SCHEMA_VERSION",
    "ADAPTIVE_PERSONA_WEIGHTING_PLAN_SCHEMA_VERSION",
    "AdaptivePersonaLayerWeight",
    "AdaptivePersonaWeightingPlan",
    "build_adaptive_persona_weighting_plan",
]
