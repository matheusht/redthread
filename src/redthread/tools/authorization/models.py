"""Authorization policy models for Phase 8C."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from redthread.orchestration.models import AuthorizationDecisionType, TrustLevel


class ArgumentRule(BaseModel):
    """Scalar argument contract enforced before policy evaluation."""

    value_type: Literal["string", "integer", "number", "boolean", "null"] = "string"
    kind: Literal["plain", "path", "command"] = "plain"
    max_length: int = 16_384
    allow_absolute: bool = False


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
    required_argument_keys: list[str] = Field(default_factory=list)
    argument_schema: dict[str, ArgumentRule] = Field(default_factory=dict)
