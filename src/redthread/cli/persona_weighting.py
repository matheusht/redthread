"""CLI helpers for persona weighting plan files."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from redthread.personas.adaptive_weighting import AdaptivePersonaWeightingPlan

UNSAFE_PROMPT_KEYS = {"raw_prompt", "raw_prompt_body", "prompt_body", "jailbreak_prompt"}


class PersonaWeightingPlanFileError(ValueError):
    """Raised when a persona weighting plan file is unsafe or malformed."""


def load_persona_weighting_plan_file(path: Path) -> dict[str, Any]:
    """Load and validate a metadata-only adaptive persona weighting plan file."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        msg = f"could not read persona weighting plan: {path}"
        raise PersonaWeightingPlanFileError(msg) from exc
    except json.JSONDecodeError as exc:
        msg = f"persona weighting plan is not valid JSON: {path}"
        raise PersonaWeightingPlanFileError(msg) from exc
    if _contains_unsafe_prompt_key(payload):
        msg = "persona weighting plan must not include raw prompt bodies"
        raise PersonaWeightingPlanFileError(msg)
    try:
        plan = AdaptivePersonaWeightingPlan.model_validate(payload)
    except ValidationError as exc:
        msg = "persona weighting plan is malformed or unsafe"
        raise PersonaWeightingPlanFileError(msg) from exc
    return plan.model_dump(mode="json")


def _contains_unsafe_prompt_key(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key) in UNSAFE_PROMPT_KEYS or _contains_unsafe_prompt_key(item)
            for key, item in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, str):
        return any(_contains_unsafe_prompt_key(item) for item in value)
    return False


__all__ = ["PersonaWeightingPlanFileError", "load_persona_weighting_plan_file"]
