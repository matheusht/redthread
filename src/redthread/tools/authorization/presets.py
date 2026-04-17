"""Least-agency policy presets for Phase 8C."""

from __future__ import annotations

from redthread.orchestration.models import AuthorizationDecisionType, TrustLevel
from redthread.tools.authorization.models import AuthorizationPolicy

RISKY_CAPABILITIES = ["shell.exec", "db.export", "db.write", "http.post"]


def default_least_agency_policies() -> list[AuthorizationPolicy]:
    return [
        AuthorizationPolicy(
            policy_id="read-only-retriever",
            actor_roles=["retriever", "analyst", "tool_executor"],
            allowed_capabilities=["lookup_status", "web.fetch", "tool.read"],
            reason="read-only retrieval is allowed",
        ),
        AuthorizationPolicy(
            policy_id="deny-risky-derived-actions",
            actor_roles=["tool_executor", "privileged_executor", "executor"],
            denied_capabilities=RISKY_CAPABILITIES,
            required_trust_levels=[TrustLevel.TRUSTED],
            decision=AuthorizationDecisionType.DENY,
            reason="derived or untrusted lineage cannot trigger risky execution",
        ),
        AuthorizationPolicy(
            policy_id="escalate-high-sensitivity-writes",
            actor_roles=["privileged_executor", "executor"],
            allowed_capabilities=["db.write"],
            max_target_sensitivity="medium",
            decision=AuthorizationDecisionType.ESCALATE,
            reason="high-sensitivity writes require explicit approval",
            require_human_approval=True,
        ),
    ]
