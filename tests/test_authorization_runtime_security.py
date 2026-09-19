from __future__ import annotations

from redthread.orchestration.models import ActionEnvelope, AuthorizationDecisionType
from redthread.tools.authorization import (
    REASON_INVALID_ARGUMENTS,
    REASON_SENSITIVITY_SPOOFED,
    AuthorizationEngine,
    default_least_agency_policies,
)
from redthread.tools.authorization.models import AuthorizationPolicy

TRUSTED_PROVENANCE = {
    "source_kind": "internal_agent",
    "trust_level": "trusted",
    "origin_id": "test-agent",
}


def test_argument_path_traversal_is_denied_before_policy_allow() -> None:
    action = ActionEnvelope(
        actor_id="retriever-1",
        actor_role="retriever",
        capability="lookup_status",
        tool_name="lookup_status",
        arguments={"path": "../../etc/shadow"},
        target_sensitivity="low",
        provenance=TRUSTED_PROVENANCE,
        requested_effect="read",
    )
    decision = AuthorizationEngine(default_least_agency_policies()).authorize(action)
    assert decision.decision == AuthorizationDecisionType.DENY
    assert decision.reason_code == REASON_INVALID_ARGUMENTS


def test_policy_argument_keys_reject_unrecognized_values() -> None:
    policy = AuthorizationPolicy(
        policy_id="tenant-read",
        actor_roles=["retriever"],
        allowed_capabilities=["lookup_status"],
        required_argument_keys=["tenant"],
    )
    action = ActionEnvelope(
        actor_id="retriever-1",
        actor_role="retriever",
        capability="lookup_status",
        tool_name="lookup_status",
        arguments={"tenant": "acme-prod", "unexpected": "value"},
        target_sensitivity="low",
        provenance=TRUSTED_PROVENANCE,
        requested_effect="read",
    )
    decision = AuthorizationEngine([policy]).authorize(action)
    assert decision.decision == AuthorizationDecisionType.DENY
    assert decision.reason_code == REASON_INVALID_ARGUMENTS


def test_authoritative_sensitivity_rejects_low_assertion() -> None:
    action = ActionEnvelope(
        actor_id="exec-2",
        actor_role="executor",
        capability="secrets.read",
        tool_name="secrets.read",
        arguments={"path": "prod/app"},
        target_sensitivity="low",
        provenance=TRUSTED_PROVENANCE,
        requested_effect="read",
    )
    decision = AuthorizationEngine(
        default_least_agency_policies(),
        sensitivity_catalog={"secrets.read": "high"},
    ).authorize(action)
    assert decision.decision == AuthorizationDecisionType.ESCALATE
    assert decision.reason_code == REASON_SENSITIVITY_SPOOFED
