"""Small policy matching helpers kept outside the authorization engine."""

from __future__ import annotations

import posixpath

from redthread.orchestration.models import (
    ActionEffect,
    ActionEnvelope,
    AuthorizationDecision,
    AuthorizationDecisionType,
)
from redthread.tools.authorization.capabilities import is_high_risk_capability
from redthread.tools.authorization.models import AuthorizationPolicy
from redthread.tools.authorization.sensitivity import (
    REASON_SENSITIVITY_SPOOFED,
    SENSITIVITY_ORDER,
)
from redthread.tools.authorization.validation import argument_keys_match_policy


def matches_denied_policy(action: ActionEnvelope, policy: AuthorizationPolicy) -> bool:
    if action.actor_role not in policy.actor_roles:
        return False
    if action.capability not in policy.denied_capabilities:
        return False
    trust = action.provenance.trust_level
    return not policy.required_trust_levels or trust not in policy.required_trust_levels


def matches_path_prefix(action: ActionEnvelope, prefixes: tuple[str, ...]) -> bool:
    path = action.arguments.get("path")
    if not isinstance(path, str):
        return False
    normalized_path = posixpath.normpath(path)
    return any(
        normalized_path == prefix or normalized_path.startswith(f"{prefix.rstrip('/')}/")
        for prefix in prefixes
    )


def matches_allowed_domain(action: ActionEnvelope, domains: tuple[str, ...]) -> bool:
    value = (
        action.arguments.get("domain")
        or action.arguments.get("host")
        or action.arguments.get("url")
    )
    if not isinstance(value, str):
        return False
    clean = value.lower().strip().removeprefix("https://").removeprefix("http://")
    clean = clean.split("/", 1)[0].split(":", 1)[0]
    return any(clean == domain or clean.endswith(f".{domain}") for domain in domains)


def matches_allowed_policy(action: ActionEnvelope, policy: AuthorizationPolicy) -> bool:
    if (
        action.actor_role not in policy.actor_roles
        or action.capability not in policy.allowed_capabilities
    ):
        return False
    if policy.allowed_path_prefixes and not matches_path_prefix(
        action, policy.allowed_path_prefixes
    ):
        return False
    if policy.allowed_domains and not matches_allowed_domain(action, policy.allowed_domains):
        return False
    return argument_keys_match_policy(action.arguments, policy)


def matches_scoped_allow_without_scope(
    action: ActionEnvelope, policies: list[AuthorizationPolicy]
) -> bool:
    return any(
        action.actor_role in policy.actor_roles
        and action.capability in policy.allowed_capabilities
        and (policy.allowed_path_prefixes or policy.allowed_domains)
        and not matches_allowed_policy(action, policy)
        for policy in policies
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
        return decision.model_copy(
            update={
                "reason_code": REASON_SENSITIVITY_SPOOFED,
                "reason": f"{REASON_SENSITIVITY_SPOOFED}: {decision.reason}",
            }
        )
    return decision.model_copy(
        update={
            "decision": AuthorizationDecisionType.DENY,
            "policy_id": "sensitivity-catalog",
            "reason_code": REASON_SENSITIVITY_SPOOFED,
            "reason": REASON_SENSITIVITY_SPOOFED,
            "matched_rules": [REASON_SENSITIVITY_SPOOFED],
            "required_escalation": False,
        }
    )


HIGH_IMPACT_EFFECTS = {
    ActionEffect.WRITE,
    ActionEffect.EXECUTE,
    ActionEffect.EXFILTRATE,
    ActionEffect.DELEGATE,
}


def requires_trusted_fallback_escalation(action: ActionEnvelope) -> bool:
    if action.requested_effect in HIGH_IMPACT_EFFECTS:
        return True
    if exceeds_sensitivity(action.target_sensitivity, "medium"):
        return True
    return is_high_risk_capability(action.capability)


def evaluate_deny_policies(
    action: ActionEnvelope, policies: list[AuthorizationPolicy]
) -> AuthorizationDecision | None:
    for policy in policies:
        if policy.denied_capabilities and matches_denied_policy(action, policy):
            return AuthorizationDecision(
                decision=AuthorizationDecisionType.DENY,
                policy_id=policy.policy_id,
                reason=policy.reason,
                matched_rules=[policy.policy_id],
                required_escalation=policy.require_human_approval,
            )
    return None


def evaluate_decision_policies(
    action: ActionEnvelope,
    policies: list[AuthorizationPolicy],
    decision: AuthorizationDecisionType,
) -> AuthorizationDecision | None:
    for policy in policies:
        if policy.decision != decision:
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

