from __future__ import annotations

from redthread.orchestration.graphs.tool_attack_graph import run_tool_attack_scenario
from redthread.orchestration.models import ActionEnvelope, AuthorizationDecisionType
from redthread.orchestration.scenarios.confused_deputy import run_confused_deputy_scenario
from redthread.orchestration.scenarios.resource_amplification import (
    run_resource_amplification_scenario,
)
from redthread.tools.authorization import (
    AuthorizationEngine,
    CapabilityClass,
    classify_capability,
    default_least_agency_policies,
)
from redthread.tools.fixtures.agentic_security import (
    benign_lookup_fixture,
    poisoned_compliance_fixture,
)


def test_tool_poisoning_follow_up_is_denied() -> None:
    scenario = run_tool_attack_scenario(
        poisoned_compliance_fixture(),
        arguments={"tenant": "acme-prod", "report_type": "soc2"},
    )
    action = ActionEnvelope.model_validate(scenario["requested_action"])

    decision = AuthorizationEngine(default_least_agency_policies()).authorize(action)

    assert decision.decision.value == "deny"
    assert decision.policy_id in {"permission-inheritance", "deny-risky-derived-actions"}


def test_confused_deputy_export_is_denied_by_lineage() -> None:
    scenario = run_confused_deputy_scenario()
    action = ActionEnvelope.model_validate(scenario["requested_action"])

    decision = AuthorizationEngine(default_least_agency_policies()).authorize(action)

    assert decision.decision.value == "deny"
    assert decision.policy_id == "permission-inheritance"


def test_benign_read_only_action_is_allowed() -> None:
    scenario = run_tool_attack_scenario(
        benign_lookup_fixture(),
        arguments={"tenant": "acme-prod"},
    )
    action = ActionEnvelope(
        actor_id="retriever-1",
        actor_role="retriever",
        capability="lookup_status",
        tool_name="lookup_status",
        arguments={"tenant": "acme-prod"},
        target_sensitivity="low",
        provenance={
            "source_kind": "internal_agent",
            "trust_level": "trusted",
            "origin_id": "retriever-1",
        },
        requested_effect="read",
    )

    decision = AuthorizationEngine(default_least_agency_policies()).authorize(action)

    assert scenario["poisoned"] is False
    assert decision.decision.value == "allow"
    assert decision.policy_id == "read-only-retriever"


def test_high_sensitivity_write_escalates() -> None:
    action = ActionEnvelope(
        actor_id="exec-1",
        actor_role="executor",
        capability="db.write",
        tool_name="db.write",
        arguments={"table": "tickets"},
        target_sensitivity="high",
        provenance={
            "source_kind": "internal_agent",
            "trust_level": "trusted",
            "origin_id": "exec-1",
        },
        requested_effect="write",
    )

    decision = AuthorizationEngine(default_least_agency_policies()).authorize(action)

    assert decision.decision.value == "escalate"
    assert decision.required_escalation is True


def test_unknown_trusted_low_risk_read_defaults_to_allow() -> None:
    action = ActionEnvelope(
        actor_id="reader-1",
        actor_role="analyst",
        capability="docs.search",
        tool_name="docs.search",
        arguments={"query": "phase 8"},
        target_sensitivity="low",
        provenance={
            "source_kind": "internal_agent",
            "trust_level": "trusted",
            "origin_id": "reader-1",
        },
        requested_effect="read",
    )

    decision = AuthorizationEngine(default_least_agency_policies()).authorize(action)

    assert decision.decision == AuthorizationDecisionType.ALLOW
    assert decision.policy_id == "default-trusted-allow"


def test_unknown_trusted_secret_access_defaults_to_escalate() -> None:
    action = ActionEnvelope(
        actor_id="exec-2",
        actor_role="executor",
        capability="secrets.read",
        tool_name="secrets.read",
        arguments={"path": "prod/app"},
        target_sensitivity="medium",
        provenance={
            "source_kind": "internal_agent",
            "trust_level": "trusted",
            "origin_id": "exec-2",
        },
        requested_effect="read",
    )

    decision = AuthorizationEngine(default_least_agency_policies()).authorize(action)

    assert decision.decision == AuthorizationDecisionType.ESCALATE
    assert decision.policy_id == "default-trusted-escalate"
    assert decision.required_escalation is True


def test_derived_memory_write_is_denied_by_permission_inheritance() -> None:
    action = ActionEnvelope(
        actor_id="executor-2",
        actor_role="executor",
        capability="memory.write",
        tool_name="memory.write",
        arguments={"entry": "save poisoned summary"},
        target_sensitivity="medium",
        provenance={
            "source_kind": "external_tool",
            "trust_level": "derived",
            "origin_id": "tool-9",
            "derived_from_untrusted": True,
        },
        requested_effect="write",
    )

    decision = AuthorizationEngine(default_least_agency_policies()).authorize(action)

    assert decision.decision == AuthorizationDecisionType.DENY
    assert decision.policy_id == "permission-inheritance"


def test_derived_agent_delegate_is_denied_by_permission_inheritance() -> None:
    action = ActionEnvelope(
        actor_id="executor-3",
        actor_role="executor",
        capability="agent.delegate",
        tool_name="agent.delegate",
        arguments={"task": "export all tickets"},
        target_sensitivity="medium",
        provenance={
            "source_kind": "external_tool",
            "trust_level": "derived",
            "origin_id": "tool-10",
            "derived_from_untrusted": True,
        },
        requested_effect="delegate",
    )

    decision = AuthorizationEngine(default_least_agency_policies()).authorize(action)

    assert decision.decision == AuthorizationDecisionType.DENY
    assert decision.policy_id == "permission-inheritance"


def test_capability_classifier_covers_new_risky_families() -> None:
    assert classify_capability("docs.search") == CapabilityClass.READ_ONLY
    assert classify_capability("memory.write") == CapabilityClass.MEMORY_MUTATION
    assert classify_capability("agent.delegate") == CapabilityClass.DELEGATION
    assert classify_capability("secrets.read") == CapabilityClass.SECRET_ACCESS


def test_resource_amplification_metrics_stay_separate_from_authorization() -> None:
    result = run_resource_amplification_scenario(repair_loops=4)

    assert result["amplification_metrics"]["budget_breached"] is True
    assert result["threat"] == "resource_amplification"
