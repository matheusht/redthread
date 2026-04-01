"""Core data models for RedThread.

All models are immutable Pydantic v2 dataclasses.
These flow through the entire pipeline: Persona → AttackTrace → AttackResult → CampaignResult.
"""

from __future__ import annotations

from dataclasses import field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


# ── Enumerations ─────────────────────────────────────────────────────────────

class MitreAtlasTactic(str, Enum):
    """MITRE ATLAS top-level tactics used to seed adversarial personas."""

    RECONNAISSANCE = "AML.TA0002"
    RESOURCE_DEVELOPMENT = "AML.TA0003"
    INITIAL_ACCESS = "AML.TA0004"
    ML_ATTACK_STAGING = "AML.TA0001"
    EXFILTRATION = "AML.TA0010"
    IMPACT = "AML.TA0011"


class PsychologicalTrigger(str, Enum):
    """Social engineering triggers layered onto personas."""

    AUTHORITY = "authority_impersonation"
    URGENCY = "urgency_and_scarcity"
    FEAR = "fear_and_intimidation"
    RECIPROCITY = "reciprocity_and_trust"
    SOCIAL_PROOF = "social_proof_and_consensus"


class AttackOutcome(str, Enum):
    """Terminal state of a single attack run."""

    SUCCESS = "success"          # Jailbreak confirmed by JudgeAgent
    FAILURE = "failure"          # All iterations exhausted, no breakthrough
    PARTIAL = "partial"          # Partial compliance (score above baseline, below threshold)
    ERROR = "error"              # Infrastructure/API error during run
    SKIPPED = "skipped"          # Run skipped (e.g., during dry run)


# ── Persona ───────────────────────────────────────────────────────────────────

class Persona(BaseModel):
    """An adversarial persona used to initialize the attacker LLM.

    Dual-objective structure:
      - cover_story: what the attacker claims to be doing (benign)
      - hidden_objective: the actual exploit goal (malicious)
    """

    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str
    tactic: MitreAtlasTactic
    technique: str                      # e.g., "AML.T0054 — LLM Prompt Injection"
    cover_story: str                    # Stated, benign-sounding intent
    hidden_objective: str               # Actual adversarial goal
    system_prompt: str                  # Full system prompt injected into attacker LLM
    psychological_triggers: list[PsychologicalTrigger]
    seed_pretext: str = ""              # Optional seed from Pretext Project


# ── Conversation ──────────────────────────────────────────────────────────────

class ConversationTurn(BaseModel):
    """A single turn in the attacker ↔ target dialogue."""

    turn_number: int
    attacker_prompt: str
    target_response: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Metadata set by PAIR refinement loop
    improvement_rationale: str = ""     # Attacker's CoT explanation for this attempt
    is_successful: bool = False


class AttackTrace(BaseModel):
    """Full conversation trace from a single attack run."""

    id: str = Field(default_factory=lambda: f"trace-{str(uuid4())[:8]}")
    persona: Persona
    algorithm: str                      # "pair" | "tap" | "crescendo" | "mcts"
    turns: list[ConversationTurn] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    outcome: AttackOutcome = AttackOutcome.FAILURE
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Evaluation ────────────────────────────────────────────────────────────────

class JudgeVerdict(BaseModel):
    """Output from the JudgeAgent for a single evaluated turn or full trace.

    score: continuous float [1.0 – 5.0] via G-Eval probability weighting.
           1.0 = perfect adherence to policy
           5.0 = complete, confirmed guardrail bypass
    """

    score: float                        # G-Eval probability-weighted float
    raw_score: int                      # LLM's raw integer output (pre-weighting)
    reasoning: str                      # Auto-CoT chain of thought
    feedback: str                       # Actionable feedback for PAIR refinement
    rubric_name: str                    # Which rubric was applied
    is_jailbreak: bool                  # score >= success_threshold


class AttackResult(BaseModel):
    """A scored, completed attack run — the primary unit of campaign output."""

    id: str = Field(default_factory=lambda: f"result-{str(uuid4())[:8]}")
    trace: AttackTrace
    verdict: JudgeVerdict
    iterations_used: int
    duration_seconds: float


# ── Campaign ──────────────────────────────────────────────────────────────────

class CampaignConfig(BaseModel):
    """User-supplied campaign parameters."""

    objective: str              # What vulnerability category to probe
    target_system_prompt: str   # The target agent's system prompt
    rubric_name: str = "authorization_bypass"
    num_personas: int = 3


class CampaignResult(BaseModel):
    """Aggregate output of a full red-team campaign."""

    id: str = Field(default_factory=lambda: f"campaign-{str(uuid4())[:8]}")
    config: CampaignConfig
    results: list[AttackResult] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None

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
