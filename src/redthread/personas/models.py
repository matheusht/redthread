"""Persona and MITRE ATLAS taxonomy models."""

from __future__ import annotations

from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class MitreAtlasTactic(str, Enum):
    """MITRE ATLAS top-level tactic identifiers used by personas."""

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


class Persona(BaseModel):
    """An adversarial persona used to initialize the attacker LLM."""

    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str
    tactic: MitreAtlasTactic
    technique: str
    cover_story: str
    hidden_objective: str
    system_prompt: str
    psychological_triggers: list[PsychologicalTrigger]
    seed_pretext: str = ""
    allowed_strategies: list[str] = Field(default_factory=list)


__all__ = ["MitreAtlasTactic", "Persona", "PsychologicalTrigger"]
