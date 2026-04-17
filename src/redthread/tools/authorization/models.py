"""Authorization policy models for Phase 8C."""

from __future__ import annotations

from pydantic import BaseModel, Field

from redthread.orchestration.models import AuthorizationDecisionType, TrustLevel


class AuthorizationPolicy(BaseModel):
    policy_id: str
    actor_roles: list[str] = Field(default_factory=list)
    allowed_capabilities: list[str] = Field(default_factory=list)
    denied_capabilities: list[str] = Field(default_factory=list)
    required_trust_levels: list[TrustLevel] = Field(default_factory=list)
    max_target_sensitivity: str = "high"
    decision: AuthorizationDecisionType = AuthorizationDecisionType.ALLOW
    reason: str = ""
    require_human_approval: bool = False
