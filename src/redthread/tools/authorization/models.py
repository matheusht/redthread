"""Authorization policy models for Phase 8C."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from redthread.orchestration.models import AuthorizationDecisionType, TrustLevel


class ArgumentRule(BaseModel):
    """Scalar argument contract enforced before policy evaluation."""

    value_type: Literal["string", "integer", "number", "boolean", "null"] = "string"
    kind: Literal["plain", "path", "command"] = "plain"
    max_length: int = 16_384
    allow_absolute: bool = False


class AuthorizationPolicy(BaseModel):
    """Immutable policy; denied capabilities are hard denies before allows."""

    model_config = ConfigDict(frozen=True)

    policy_id: str
    actor_roles: tuple[str, ...] = ()
    allowed_capabilities: tuple[str, ...] = ()
    denied_capabilities: tuple[str, ...] = ()
    required_trust_levels: tuple[TrustLevel, ...] = ()
    max_target_sensitivity: str = "high"
    decision: AuthorizationDecisionType = AuthorizationDecisionType.ALLOW
    reason: str = ""
    require_human_approval: bool = False
    required_argument_keys: list[str] = Field(default_factory=list)
    argument_schema: dict[str, ArgumentRule] = Field(default_factory=dict)
    allowed_path_prefixes: tuple[str, ...] = ()
    allowed_domains: tuple[str, ...] = ()
