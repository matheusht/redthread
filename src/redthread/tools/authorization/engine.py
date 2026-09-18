"""Deterministic authorization engine for Phase 8C."""

from __future__ import annotations

from collections.abc import Mapping

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
from redthread.tools.authorization.policy_matching import (
    apply_sensitivity_guard,
    exceeds_sensitivity,
    matches_allowed_policy,
    matches_denied_policy,
)
from redthread.tools.authorization.sensitivity import (
    DEFAULT_SENSITIVITY_CATALOG,
    authoritative_sensitivity,
    sensitivity_value,
)
from redthread.tools.authorization.validation import (
    DEFAULT_ARGUMENT_SCHEMAS,
    REASON_INVALID_ARGUMENTS,
    validate_arguments,
)

HIGH_IMPACT_EFFECTS = {
    ActionEffect.WRITE,
    ActionEffect.EXECUTE,
    ActionEffect.EXFILTRATE,
    ActionEffect.DELEGATE,
}


class AuthorizationEngine:
    def __init__(
        self,
        policies: list[AuthorizationPolicy],
        sensitivity_catalog: Mapping[str, str] | None = None,
    ) -> None:
        self.policies = policies
        self.sensitivity_catalog = dict(DEFAULT_SENSITIVITY_CATALOG)
        self.sensitivity_catalog.update(sensitivity_catalog or {})
        self.argument_schemas = DEFAULT_ARGUMENT_SCHEMAS

    def authorize(self, action: ActionEnvelope) -> AuthorizationDecision:
        if violates_permission_inheritance(action.provenance, action.capability):
            return AuthorizationDecision(
                decision=AuthorizationDecisionType.DENY,
                policy_id="permission-inheritance",
                reason="derived untrusted lineage cannot request this capability",
                matched_rules=["permission_inheritance"],
            )

        invalid_reason = validate_arguments(
            action.arguments,
            action.actor_role,
            action.capability,
            self.policies,
            self.argument_schemas,
        )
        if invalid_reason:
            return AuthorizationDecision(
                decision=AuthorizationDecisionType.DENY,
                policy_id="invalid-arguments",
                reason=f"{REASON_INVALID_ARGUMENTS}: {invalid_reason}",
                reason_code=REASON_INVALID_ARGUMENTS,
                matched_rules=[REASON_INVALID_ARGUMENTS],
            )

        authoritative = authoritative_sensitivity(action, self.sensitivity_catalog)
        sensitivity_spoofed = False
        if authoritative is not None:
            asserted = sensitivity_value(action.target_sensitivity)
            if asserted < sensitivity_value(authoritative):
                sensitivity_spoofed = True
            action = action.model_copy(update={"target_sensitivity": max(
                action.target_sensitivity,
                authoritative,
                key=sensitivity_value,
            )})

        decision = self._evaluate_deny_policies(action)
        if decision is not None:
            return apply_sensitivity_guard(decision, sensitivity_spoofed)

        decision = self._evaluate_escalate_policies(action)
        if decision is not None:
            return apply_sensitivity_guard(decision, sensitivity_spoofed)

        decision = self._evaluate_allow_policies(action)
        if decision is not None:
            return apply_sensitivity_guard(decision, sensitivity_spoofed)

        if action.provenance.trust_level in {TrustLevel.UNTRUSTED, TrustLevel.DERIVED}:
            return apply_sensitivity_guard(AuthorizationDecision(
                decision=AuthorizationDecisionType.DENY,
                policy_id="default-derived-deny",
                reason="no matching allow policy for derived or untrusted action",
                matched_rules=["default-derived-deny"],
            ), sensitivity_spoofed)

        if self._requires_trusted_fallback_escalation(action):
            return apply_sensitivity_guard(AuthorizationDecision(
                decision=AuthorizationDecisionType.ESCALATE,
                policy_id="default-trusted-escalate",
                reason="trusted action is unknown and high-impact; explicit approval required",
                matched_rules=["default-trusted-escalate"],
                required_escalation=True,
            ), sensitivity_spoofed)

        return apply_sensitivity_guard(AuthorizationDecision(
            decision=AuthorizationDecisionType.ALLOW,
            policy_id="default-trusted-allow",
            reason="trusted low-risk read action with no conflicting policy",
            matched_rules=["default-trusted-allow"],
        ), sensitivity_spoofed)

    def _evaluate_deny_policies(self, action: ActionEnvelope) -> AuthorizationDecision | None:
        for policy in self.policies:
            if policy.decision != AuthorizationDecisionType.DENY:
                continue
            if not matches_denied_policy(action, policy):
                continue
            return AuthorizationDecision(
                decision=policy.decision,
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
            if not matches_allowed_policy(action, policy):
                continue
            if exceeds_sensitivity(action.target_sensitivity, policy.max_target_sensitivity):
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
            if not matches_allowed_policy(action, policy):
                continue
            if exceeds_sensitivity(action.target_sensitivity, policy.max_target_sensitivity):
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

    def _requires_trusted_fallback_escalation(self, action: ActionEnvelope) -> bool:
        if action.requested_effect in HIGH_IMPACT_EFFECTS:
            return True
        if exceeds_sensitivity(action.target_sensitivity, "medium"):
            return True
        return is_high_risk_capability(action.capability)
