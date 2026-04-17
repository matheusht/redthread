"""Deterministic authorization engine for Phase 8C."""

from __future__ import annotations

from redthread.orchestration.models import (
    ActionEffect,
    ActionEnvelope,
    AuthorizationDecision,
    AuthorizationDecisionType,
    TrustLevel,
)
from redthread.orchestration.permission_inheritance import (
    violates_permission_inheritance,
)
from redthread.tools.authorization.models import AuthorizationPolicy

SENSITIVITY_ORDER = {"low": 0, "medium": 1, "high": 2}
RISKY_CAPABILITY_PREFIXES = (
    "shell.",
    "db.",
    "http.",
    "prompt.",
    "agent.",
    "memory.",
)
HIGH_IMPACT_EFFECTS = {
    ActionEffect.WRITE,
    ActionEffect.EXECUTE,
    ActionEffect.EXFILTRATE,
    ActionEffect.DELEGATE,
}


class AuthorizationEngine:
    def __init__(self, policies: list[AuthorizationPolicy]) -> None:
        self.policies = policies

    def authorize(self, action: ActionEnvelope) -> AuthorizationDecision:
        if violates_permission_inheritance(action.provenance, action.capability):
            return AuthorizationDecision(
                decision=AuthorizationDecisionType.DENY,
                policy_id="permission-inheritance",
                reason="derived untrusted lineage cannot request this capability",
                matched_rules=["permission_inheritance"],
            )

        for policy in self.policies:
            if action.actor_role not in policy.actor_roles:
                continue
            if policy.allowed_capabilities and action.capability not in policy.allowed_capabilities:
                continue
            if policy.denied_capabilities and action.capability in policy.denied_capabilities:
                trust = action.provenance.trust_level
                if policy.required_trust_levels and trust not in policy.required_trust_levels:
                    return AuthorizationDecision(
                        decision=policy.decision,
                        policy_id=policy.policy_id,
                        reason=policy.reason,
                        matched_rules=[policy.policy_id],
                        required_escalation=policy.require_human_approval,
                    )
            elif policy.allowed_capabilities:
                if self._exceeds_sensitivity(action.target_sensitivity, policy.max_target_sensitivity):
                    return AuthorizationDecision(
                        decision=AuthorizationDecisionType.ESCALATE,
                        policy_id=policy.policy_id,
                        reason="target sensitivity exceeds preset allowance",
                        matched_rules=[policy.policy_id],
                        required_escalation=True,
                    )
                return AuthorizationDecision(
                    decision=policy.decision,
                    policy_id=policy.policy_id,
                    reason=policy.reason,
                    matched_rules=[policy.policy_id],
                    required_escalation=policy.require_human_approval,
                )

        if action.provenance.trust_level in {TrustLevel.UNTRUSTED, TrustLevel.DERIVED}:
            return AuthorizationDecision(
                decision=AuthorizationDecisionType.DENY,
                policy_id="default-derived-deny",
                reason="no matching allow policy for derived or untrusted action",
                matched_rules=["default-derived-deny"],
            )

        if self._requires_trusted_fallback_escalation(action):
            return AuthorizationDecision(
                decision=AuthorizationDecisionType.ESCALATE,
                policy_id="default-trusted-escalate",
                reason="trusted action is unknown and high-impact; explicit approval required",
                matched_rules=["default-trusted-escalate"],
                required_escalation=True,
            )

        return AuthorizationDecision(
            decision=AuthorizationDecisionType.ALLOW,
            policy_id="default-trusted-allow",
            reason="trusted low-risk read action with no conflicting policy",
            matched_rules=["default-trusted-allow"],
        )

    def _exceeds_sensitivity(self, actual: str, maximum: str) -> bool:
        return SENSITIVITY_ORDER.get(actual, 2) > SENSITIVITY_ORDER.get(maximum, 2)

    def _requires_trusted_fallback_escalation(self, action: ActionEnvelope) -> bool:
        if action.requested_effect in HIGH_IMPACT_EFFECTS:
            return True
        if self._exceeds_sensitivity(action.target_sensitivity, "medium"):
            return True
        return action.capability.startswith(RISKY_CAPABILITY_PREFIXES)
