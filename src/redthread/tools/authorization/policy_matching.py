"""Small policy matching helpers kept outside the authorization engine."""

from __future__ import annotations

from redthread.orchestration.models import (
    ActionEnvelope,
    AuthorizationDecision,
    AuthorizationDecisionType,
)
from redthread.tools.authorization.models import AuthorizationPolicy
from redthread.tools.authorization.sensitivity import (
    REASON_SENSITIVITY_SPOOFED,
    SENSITIVITY_ORDER,
)


def matches_denied_policy(action: ActionEnvelope, policy: AuthorizationPolicy) -> bool:
    if action.actor_role not in policy.actor_roles:
        return False
    if action.capability not in policy.denied_capabilities:
        return False
    trust = action.provenance.trust_level
    return not policy.required_trust_levels or trust not in policy.required_trust_levels


def matches_allowed_policy(action: ActionEnvelope, policy: AuthorizationPolicy) -> bool:
    if action.actor_role not in policy.actor_roles or action.capability not in policy.allowed_capabilities:
        return False
    keys = set(action.arguments)
    declared_keys = set(policy.argument_schema)
    return (
        (not declared_keys or keys.issubset(declared_keys))
        and set(policy.required_argument_keys).issubset(keys)
    )


def exceeds_sensitivity(actual: str, maximum: str) -> bool:
    return SENSITIVITY_ORDER.get(actual, 2) > SENSITIVITY_ORDER.get(maximum, 2)


def apply_sensitivity_guard(
    decision: AuthorizationDecision,
    spoofed: bool,
) -> AuthorizationDecision:
    if not spoofed:
        return decision
    if decision.decision == AuthorizationDecisionType.ESCALATE:
        return decision.model_copy(update={
            "reason_code": REASON_SENSITIVITY_SPOOFED,
            "reason": f"{REASON_SENSITIVITY_SPOOFED}: {decision.reason}",
        })
    return decision.model_copy(update={
        "decision": AuthorizationDecisionType.DENY,
        "policy_id": "sensitivity-catalog",
        "reason_code": REASON_SENSITIVITY_SPOOFED,
        "reason": REASON_SENSITIVITY_SPOOFED,
        "matched_rules": [REASON_SENSITIVITY_SPOOFED],
        "required_escalation": False,
    })
