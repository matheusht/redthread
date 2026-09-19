"""Shared immutable models for curated golden evaluation traces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class GoldenTurn:
    """One attacker/target exchange within a curated trace."""

    attacker_prompt: str
    target_response: str


@dataclass(frozen=True)
class GoldenTrace:
    """A single curated test case with verified expected outcome."""

    id: str
    category: Literal["jailbreak_confirmed", "safe_refusal", "guardrail_validated"]
    objective: str
    system_prompt: str
    attacker_prompt: str
    target_response: str
    expected_score_min: float
    expected_score_max: float
    tactic: str
    rationale: str
    turns: tuple[GoldenTurn, ...] = ()

    @property
    def evaluation_turns(self) -> tuple[GoldenTurn, ...]:
        """Return explicit multi-turn evidence, or the legacy single turn."""
        if self.turns:
            return self.turns
        return (GoldenTurn(self.attacker_prompt, self.target_response),)
