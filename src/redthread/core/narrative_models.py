"""Narrative adaptation models for Crescendo's phase-aware strategy layer.

These are pure data containers — no behavior.
Policy logic lives in narrative_policy.py.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class NarrativePhase(str, Enum):
    """Ordered phases of a Crescendo narrative arc."""

    RAPPORT = "rapport"          # Turns 1-2: benign, establish trust
    LEGITIMACY = "legitimacy"    # Turns 3-4: credentials, plausibility
    PRESSURE = "pressure"        # Turns 5-7: urgency, need, stakes
    ASK = "ask"                  # Turns 8+:  the actual objective request

    def next(self) -> NarrativePhase:
        """Advance to the next phase (capped at ASK)."""
        order = list(NarrativePhase)
        idx = order.index(self)
        return order[min(idx + 1, len(order) - 1)]


class NarrativeState(BaseModel):
    """Mutable narrative state tracked across Crescendo turns.

    Updated by NarrativeAdaptationPolicy.update() after each accepted turn.
    Serialized into trace.metadata["narrative_state"] at end of run.
    """

    phase: NarrativePhase = NarrativePhase.RAPPORT
    used_strategies: list[str] = Field(default_factory=list)
    successful_strategies: list[str] = Field(default_factory=list)
    failed_strategies: list[str] = Field(default_factory=list)
    pivot_count: int = 0
    consecutive_failures: int = 0
    last_refusal_signal: str | None = None
    turn_count: int = 0


class NarrativeGuidance(BaseModel):
    """Policy output: what Crescendo should do on the next turn.

    Injected as a ## Narrative Guidance section in the attacker prompt.
    """

    recommended_strategy: str
    phase_action: Literal["hold", "escalate", "pivot"]
    framing_hint: str           # Short directive for the attacker LLM
    avoid_patterns: list[str]   # Strategies proven to fail — attacker should skip these
