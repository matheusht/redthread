"""Core data models for RedThread.

All models are immutable Pydantic v2 dataclasses.
These flow through the entire pipeline: Persona → AttackTrace → AttackResult → CampaignResult.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from redthread.core.models import AttackNode as AttackNode
from redthread.core.models import CrescendoTurn as CrescendoTurn
from redthread.core.models import MCTSNode as MCTSNode
from redthread.personas.models import MitreAtlasTactic as MitreAtlasTactic
from redthread.personas.models import Persona as Persona
from redthread.personas.models import PsychologicalTrigger as PsychologicalTrigger


class AttackOutcome(str, Enum):
    """Terminal state of a single attack run."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    ERROR = "error"
    SKIPPED = "skipped"


class ConversationTurn(BaseModel):
    """A single turn in the attacker ↔ target dialogue."""

    turn_number: int
    attacker_prompt: str
    target_response: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    improvement_rationale: str = ""
    is_successful: bool = False


class AttackTrace(BaseModel):
    """Full conversation trace from a single attack run."""

    id: str = Field(default_factory=lambda: f"trace-{str(uuid4())[:8]}")
    persona: Persona
    algorithm: str
    turns: list[ConversationTurn] = Field(default_factory=list)
    nodes: list[AttackNode] = Field(default_factory=list)
    crescendo_turns: list[CrescendoTurn] = Field(default_factory=list)
    mcts_nodes: list[MCTSNode] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    outcome: AttackOutcome = AttackOutcome.FAILURE
    metadata: dict[str, Any] = Field(default_factory=dict)


class JudgeVerdict(BaseModel):
    """Output from the JudgeAgent for a single evaluated turn or full trace.

    score: continuous float [1.0 – 5.0] via G-Eval probability weighting.
           1.0 = perfect adherence to policy
           5.0 = complete, confirmed guardrail bypass
    """

    score: float
    raw_score: int
    reasoning: str
    feedback: str
    rubric_name: str
    is_jailbreak: bool


class AttackResult(BaseModel):
    """A scored, completed attack run — the primary unit of campaign output."""

    id: str = Field(default_factory=lambda: f"result-{str(uuid4())[:8]}")
    trace: AttackTrace
    verdict: JudgeVerdict
    iterations_used: int
    duration_seconds: float


class CampaignConfig(BaseModel):
    """User-supplied campaign parameters."""

    objective: str
    target_system_prompt: str
    rubric_name: str = "authorization_bypass"
    num_personas: int = 3
    prompting_layer_profile: dict[str, Any] = Field(default_factory=dict)
    persona_weighting_plan: dict[str, Any] = Field(default_factory=dict)


class CampaignResult(BaseModel):
    """Aggregate output of a full red-team campaign."""

    id: str = Field(default_factory=lambda: f"campaign-{str(uuid4())[:8]}")
    config: CampaignConfig
    results: list[AttackResult] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def attack_success_rate(self) -> float:
        """ASR: % of runs where JudgeAgent confirmed a jailbreak."""
        if not self.results:
            return 0.0
        successes = sum(1 for r in self.results if r.verdict.is_jailbreak)
        return successes / len(self.results)

    @property
    def average_score(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.verdict.score for r in self.results) / len(self.results)
