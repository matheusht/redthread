from __future__ import annotations

from redthread.orchestration.graphs.tool_attack_graph import run_tool_attack_scenario
from redthread.orchestration.models import ActionEnvelope
from redthread.orchestration.scenarios.confused_deputy import run_confused_deputy_scenario
from redthread.orchestration.scenarios.resource_amplification import (
    run_resource_amplification_scenario,
)
from redthread.tools.authorization import AuthorizationEngine, default_least_agency_policies
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


def test_resource_amplification_metrics_stay_separate_from_authorization() -> None:
    result = run_resource_amplification_scenario(repair_loops=4)

    assert result["amplification_metrics"]["budget_breached"] is True
    assert result["threat"] == "resource_amplification"
