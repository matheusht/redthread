"""Authorization policy models for Phase 8C."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from redthread.orchestration.models import AuthorizationDecisionType, TrustLevel


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
    allowed_path_prefixes: tuple[str, ...] = ()
    allowed_domains: tuple[str, ...] = ()
