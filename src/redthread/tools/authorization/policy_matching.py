"""Small policy matching helpers kept outside the authorization engine."""

from __future__ import annotations

import posixpath

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
