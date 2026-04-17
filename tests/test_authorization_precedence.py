from __future__ import annotations

from redthread.orchestration.models import (
    ActionEnvelope,
    AuthorizationDecisionType,
    TrustLevel,
)
from redthread.tools.authorization import AuthorizationEngine
from redthread.tools.authorization.models import AuthorizationPolicy


TRUSTED_PROVENANCE = {
    "source_kind": "internal_agent",
    "trust_level": "trusted",
    "origin_id": "exec-1",
}
DERIVED_PROVENANCE = {
    "source_kind": "external_tool",
    "trust_level": "derived",
    "origin_id": "tool-1",
}


def test_deny_policy_beats_allow_policy() -> None:
    engine = AuthorizationEngine(
        [
            AuthorizationPolicy(
                policy_id="allow-docs-search",
                actor_roles=["executor"],
                allowed_capabilities=["docs.search"],
                decision=AuthorizationDecisionType.ALLOW,
                reason="generic allow",
            ),
            AuthorizationPolicy(
                policy_id="deny-derived-docs-search",
                actor_roles=["executor"],
                denied_capabilities=["docs.search"],
                required_trust_levels=[TrustLevel.TRUSTED],
                decision=AuthorizationDecisionType.DENY,
                reason="derived docs access denied",
            ),
        ]
    )
    action = ActionEnvelope(
        actor_id="exec-1",
        actor_role="executor",
        capability="docs.search",
        tool_name="docs.search",
        target_sensitivity="low",
        provenance=DERIVED_PROVENANCE,
        requested_effect="read",
    )

    decision = engine.authorize(action)

    assert decision.decision == AuthorizationDecisionType.DENY
    assert decision.policy_id == "deny-derived-docs-search"


def test_escalate_policy_beats_generic_allow_policy() -> None:
    engine = AuthorizationEngine(
        [
            AuthorizationPolicy(
                policy_id="escalate-memory-write",
                actor_roles=["executor"],
                allowed_capabilities=["memory.write"],
                decision=AuthorizationDecisionType.ESCALATE,
                reason="memory writes need approval",
                require_human_approval=True,
            ),
            AuthorizationPolicy(
                policy_id="allow-memory-write",
                actor_roles=["executor"],
                allowed_capabilities=["memory.write"],
                decision=AuthorizationDecisionType.ALLOW,
                reason="broad allow",
            ),
        ]
    )
    action = ActionEnvelope(
        actor_id="exec-2",
        actor_role="executor",
        capability="memory.write",
        tool_name="memory.write",
        target_sensitivity="low",
        provenance=TRUSTED_PROVENANCE,
        requested_effect="write",
    )

    decision = engine.authorize(action)

    assert decision.decision == AuthorizationDecisionType.ESCALATE
    assert decision.policy_id == "escalate-memory-write"
    assert decision.required_escalation is True


def test_explicit_allow_beats_fallback_when_policy_matches() -> None:
    engine = AuthorizationEngine(
        [
            AuthorizationPolicy(
                policy_id="allow-docs-search",
                actor_roles=["analyst"],
                allowed_capabilities=["docs.search"],
                decision=AuthorizationDecisionType.ALLOW,
                reason="docs search is safe",
            )
        ]
    )
    action = ActionEnvelope(
        actor_id="analyst-1",
        actor_role="analyst",
        capability="docs.search",
        tool_name="docs.search",
        target_sensitivity="low",
        provenance=TRUSTED_PROVENANCE,
        requested_effect="read",
    )

    decision = engine.authorize(action)

    assert decision.decision == AuthorizationDecisionType.ALLOW
    assert decision.policy_id == "allow-docs-search"
