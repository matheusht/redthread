"""Persona telemetry report artifact helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from redthread.personas.adaptive_weighting import build_adaptive_persona_weighting_plan
from redthread.personas.outcomes import PersonaOutcomeTelemetry

PERSONA_OUTCOMES_NAME = "persona-outcomes.json"
ADAPTIVE_PERSONA_WEIGHTING_PLAN_NAME = "adaptive-persona-weighting-plan.json"


def persona_artifacts_from_metadata(metadata: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Build safe persona report artifacts from campaign metadata."""
    raw = metadata.get("persona_outcome_telemetry", {})
    if not isinstance(raw, Mapping) or not raw:
        return {
            "persona_outcome_telemetry": {},
            "adaptive_persona_weighting_plan": {},
        }
    telemetry = PersonaOutcomeTelemetry.model_validate(raw)
    plan = build_adaptive_persona_weighting_plan(telemetry)
    return {
        "persona_outcome_telemetry": telemetry.model_dump(mode="json"),
        "adaptive_persona_weighting_plan": plan.model_dump(mode="json"),
    }


__all__ = [
    "ADAPTIVE_PERSONA_WEIGHTING_PLAN_NAME",
    "PERSONA_OUTCOMES_NAME",
    "persona_artifacts_from_metadata",
]
