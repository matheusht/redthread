"""Deterministic authorization engine for Phase 8C."""

from __future__ import annotations

import posixpath

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
from redthread.tools.authorization.capabilities import is_high_risk_capability
from redthread.tools.authorization.models import AuthorizationPolicy

SENSITIVITY_ORDER = {"low": 0, "medium": 1, "high": 2}
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

        decision = self._evaluate_deny_policies(action)
        if decision is not None:
            return decision

        decision = self._evaluate_escalate_policies(action)
        if decision is not None:
            return decision

        if self._matches_scoped_allow_without_scope(action):
            return AuthorizationDecision(
                decision=AuthorizationDecisionType.DENY,
                policy_id="scope-boundary",
                reason="action target is outside the policy allowlist",
                matched_rules=["scope_boundary"],
            )

        decision = self._evaluate_allow_policies(action)
        if decision is not None:
            return decision

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

    def _evaluate_deny_policies(self, action: ActionEnvelope) -> AuthorizationDecision | None:
        for policy in self.policies:
            if not policy.denied_capabilities:
                continue
            if not self._matches_denied_policy(action, policy):
                continue
            return AuthorizationDecision(
                decision=AuthorizationDecisionType.DENY,
                policy_id=policy.policy_id,
                reason=policy.reason,
                matched_rules=[policy.policy_id],
                required_escalation=policy.require_human_approval,
            )
        return None

    def _evaluate_escalate_policies(self, action: ActionEnvelope) -> AuthorizationDecision | None:
        for policy in self.policies:
            if policy.decision != AuthorizationDecisionType.ESCALATE:
                continue
            if not self._matches_allowed_policy(action, policy):
                continue
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
        return None

    def _evaluate_allow_policies(self, action: ActionEnvelope) -> AuthorizationDecision | None:
        for policy in self.policies:
            if policy.decision != AuthorizationDecisionType.ALLOW:
                continue
            if not self._matches_allowed_policy(action, policy):
                continue
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
        return None

    def _matches_denied_policy(self, action: ActionEnvelope, policy: AuthorizationPolicy) -> bool:
        if action.actor_role not in policy.actor_roles:
            return False
        if action.capability not in policy.denied_capabilities:
            return False
        trust = action.provenance.trust_level
        return not policy.required_trust_levels or trust not in policy.required_trust_levels

    def _matches_allowed_policy(self, action: ActionEnvelope, policy: AuthorizationPolicy) -> bool:
        if action.actor_role not in policy.actor_roles or action.capability not in policy.allowed_capabilities:
            return False
        if policy.allowed_path_prefixes and not self._matches_path_prefix(action, policy.allowed_path_prefixes):
            return False
        return not policy.allowed_domains or self._matches_allowed_domain(action, policy.allowed_domains)

    def _matches_scoped_allow_without_scope(self, action: ActionEnvelope) -> bool:
        return any(
            action.actor_role in policy.actor_roles
            and action.capability in policy.allowed_capabilities
            and (policy.allowed_path_prefixes or policy.allowed_domains)
            and not self._matches_allowed_policy(action, policy)
            for policy in self.policies
        )

    @staticmethod
    def _matches_path_prefix(action: ActionEnvelope, prefixes: tuple[str, ...]) -> bool:
        path = action.arguments.get("path")
        if not isinstance(path, str):
            return False
        normalized_path = posixpath.normpath(path)
        return any(
            normalized_path == prefix
            or normalized_path.startswith(f"{prefix.rstrip('/')}/")
            for prefix in prefixes
        )

    @staticmethod
    def _matches_allowed_domain(action: ActionEnvelope, domains: tuple[str, ...]) -> bool:
        value = action.arguments.get("domain") or action.arguments.get("host") or action.arguments.get("url")
        if not isinstance(value, str):
            return False
        clean = value.lower().strip().removeprefix("https://").removeprefix("http://")
        clean = clean.split("/", 1)[0].split(":", 1)[0]
        return any(clean == domain or clean.endswith(f".{domain}") for domain in domains)

    def _exceeds_sensitivity(self, actual: str, maximum: str) -> bool:
        return SENSITIVITY_ORDER.get(actual, 2) > SENSITIVITY_ORDER.get(maximum, 2)

    def _requires_trusted_fallback_escalation(self, action: ActionEnvelope) -> bool:
        if action.requested_effect in HIGH_IMPACT_EFFECTS:
            return True
        if self._exceeds_sensitivity(action.target_sensitivity, "medium"):
            return True
        return is_high_risk_capability(action.capability)
