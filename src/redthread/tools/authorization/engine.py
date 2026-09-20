"""Deterministic authorization engine for Phase 8C."""

from __future__ import annotations

from collections.abc import Mapping

from redthread.orchestration.models import (
    ActionEnvelope,
    AuthorizationDecision,
    AuthorizationDecisionType,
    TrustLevel,
)
from redthread.orchestration.permission_inheritance import (
    violates_permission_inheritance,
)
from redthread.tools.authorization.audit import AuditLogger, AuthorizationAuditRecord
from redthread.tools.authorization.models import AuthorizationPolicy
from redthread.tools.authorization.policy_matching import (
    apply_sensitivity_guard,
    evaluate_decision_policies,
    evaluate_deny_policies,
    matches_scoped_allow_without_scope,
    requires_trusted_fallback_escalation,
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


class AuthorizationEngine:
    """Deterministic policy enforcement engine with immutable audit logging."""

    def __init__(
        self,
        policies: list[AuthorizationPolicy],
        sensitivity_catalog: Mapping[str, str] | None = None,
        max_audit_records: int = 1000,
    ) -> None:
        self.policies = policies
        self.sensitivity_catalog = dict(DEFAULT_SENSITIVITY_CATALOG)
        self.sensitivity_catalog.update(sensitivity_catalog or {})
        self.argument_schemas = DEFAULT_ARGUMENT_SCHEMAS
        self._audit_logger = AuditLogger(max_records=max_audit_records)

    def authorize(self, action: ActionEnvelope) -> AuthorizationDecision:
        decision = self._compute_decision(action)
        self._audit_logger.record(action, decision)
        return decision

    def get_audit_records(self) -> list[AuthorizationAuditRecord]:
        """Retrieve chronological immutable audit records."""
        return self._audit_logger.get_records()

    def clear_audit_records(self) -> None:
        """Clear the recorded audit trail."""
        self._audit_logger.clear()

    def _compute_decision(self, action: ActionEnvelope) -> AuthorizationDecision:
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
            action = action.model_copy(
                update={
                    "target_sensitivity": max(
                        action.target_sensitivity, authoritative, key=sensitivity_value
                    )
                }
            )

        decision = evaluate_deny_policies(action, self.policies)
        if decision is not None:
            return apply_sensitivity_guard(decision, sensitivity_spoofed)

        decision = evaluate_decision_policies(
            action, self.policies, AuthorizationDecisionType.ESCALATE
        )
        if decision is not None:
            return apply_sensitivity_guard(decision, sensitivity_spoofed)

        if matches_scoped_allow_without_scope(action, self.policies):
            return AuthorizationDecision(
                decision=AuthorizationDecisionType.DENY,
                policy_id="scope-boundary",
                reason="action target is outside the policy allowlist",
                matched_rules=["scope_boundary"],
            )

        decision = evaluate_decision_policies(
            action, self.policies, AuthorizationDecisionType.ALLOW
        )
        if decision is not None:
            return apply_sensitivity_guard(decision, sensitivity_spoofed)

        if action.provenance.trust_level in {TrustLevel.UNTRUSTED, TrustLevel.DERIVED}:
            return apply_sensitivity_guard(
                AuthorizationDecision(
                    decision=AuthorizationDecisionType.DENY,
                    policy_id="default-derived-deny",
                    reason="no matching allow policy for derived or untrusted action",
                    matched_rules=["default-derived-deny"],
                ),
                sensitivity_spoofed,
            )

        if requires_trusted_fallback_escalation(action):
            return apply_sensitivity_guard(
                AuthorizationDecision(
                    decision=AuthorizationDecisionType.ESCALATE,
                    policy_id="default-trusted-escalate",
                    reason="trusted action is unknown and high-impact; explicit approval required",
                    matched_rules=["default-trusted-escalate"],
                    required_escalation=True,
                ),
                sensitivity_spoofed,
            )

        return apply_sensitivity_guard(
            AuthorizationDecision(
                decision=AuthorizationDecisionType.ALLOW,
                policy_id="default-trusted-allow",
                reason="trusted low-risk read action with no conflicting policy",
                matched_rules=["default-trusted-allow"],
            ),
            sensitivity_spoofed,
        )
