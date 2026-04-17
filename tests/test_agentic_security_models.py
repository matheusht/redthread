from __future__ import annotations

from redthread.orchestration.models import (
    ActionEffect,
    ActionEnvelope,
    AgenticSecurityThreat,
    AmplificationMetrics,
    AuthorizationDecision,
    AuthorizationDecisionType,
    BoundaryCrossing,
    BoundaryType,
    ProvenanceRecord,
    ProvenanceSourceKind,
    TrustLevel,
)
import pytest

from redthread.orchestration.runtime_summary import build_runtime_summary


def test_agentic_threat_taxonomy_uses_stable_values() -> None:
    assert AgenticSecurityThreat.TOOL_POISONING.value == "tool_poisoning"
    assert AgenticSecurityThreat.CONFUSED_DEPUTY.value == "confused_deputy"
    assert AgenticSecurityThreat.RESOURCE_AMPLIFICATION.value == "resource_amplification"


def test_action_envelope_serializes_provenance_and_authorization() -> None:
    provenance = ProvenanceRecord(
        source_kind=ProvenanceSourceKind.EXTERNAL_TOOL,
        trust_level=TrustLevel.UNTRUSTED,
        origin_id="tool-001",
        parent_ids=["req-001"],
        boundary_crossings=[
            BoundaryCrossing(boundary=BoundaryType.TOOL_RETURN, detail="tool output entered context"),
            BoundaryCrossing(boundary=BoundaryType.SHARED_STATE, detail="summary stored in workflow state"),
        ],
        canary_tags=["CANARY_EXT_TOOL_01"],
        derived_from_untrusted=True,
    )
    decision = AuthorizationDecision(
        decision=AuthorizationDecisionType.DENY,
        policy_id="deny-external-shell",
        reason="untrusted lineage cannot trigger shell execution",
        matched_rules=["external_untrusted_no_exec"],
    )

    envelope = ActionEnvelope(
        actor_id="exec-agent",
        actor_role="executor",
        capability="shell.exec",
        tool_name="shell.exec",
        arguments={"command": "cat /workspace/.env"},
        target_sensitivity="high",
        provenance=provenance,
        requested_effect=ActionEffect.EXECUTE,
        authorization_status=decision.decision,
        authorization_reason=decision.reason,
        requires_human_approval=True,
        canary_tags=["CANARY_EXT_TOOL_01"],
    )

    dumped = envelope.model_dump(mode="json")

    assert dumped["provenance"]["source_kind"] == "external_tool"
    assert dumped["provenance"]["derived_from_untrusted"] is True
    assert dumped["authorization_status"] == "deny"
    assert dumped["requested_effect"] == "execute"
    assert dumped["canary_tags"] == ["CANARY_EXT_TOOL_01"]
    assert envelope.provenance.crossed_boundary_count == 2
    assert envelope.provenance.has_untrusted_lineage is True


def test_provenance_normalizes_derived_flag_from_trust_level() -> None:
    provenance = ProvenanceRecord(
        source_kind=ProvenanceSourceKind.EXTERNAL_DOCUMENT,
        trust_level=TrustLevel.DERIVED,
        origin_id="doc-1",
        derived_from_untrusted=False,
    )

    assert provenance.derived_from_untrusted is True
    assert provenance.has_untrusted_lineage is True


def test_provenance_rejects_trusted_contradiction() -> None:
    with pytest.raises(ValueError, match="trusted provenance cannot also be marked"):
        ProvenanceRecord(
            source_kind=ProvenanceSourceKind.INTERNAL_AGENT,
            trust_level=TrustLevel.TRUSTED,
            origin_id="agent-1",
            derived_from_untrusted=True,
        )


def test_amplification_metrics_default_to_safe_baseline() -> None:
    metrics = AmplificationMetrics()

    assert metrics.tool_call_count == 0
    assert metrics.token_growth_ratio == 1.0
    assert metrics.budget_breached is False


def test_runtime_summary_exposes_agentic_security_fields_when_present() -> None:
    summary = build_runtime_summary(
        {
            "attack_worker_total": 1,
            "errors": [],
            "agentic_action_total": 3,
            "authorization_decision_counts": {"allow": 1, "deny": 2},
            "canary_event_total": 2,
            "amplification_metrics": {"tool_call_count": 5, "budget_breached": True},
            "untrusted_lineage_action_total": 2,
        }
    )

    assert summary["agentic_security"]["action_total"] == 3
    assert summary["agentic_security"]["authorization_decision_counts"]["deny"] == 2
    assert summary["agentic_security"]["canary_event_total"] == 2
    assert summary["agentic_security"]["amplification_metrics"]["budget_breached"] is True
    assert summary["agentic_security"]["untrusted_lineage_action_total"] == 2


def test_runtime_summary_defaults_agentic_security_to_empty_shape() -> None:
    summary = build_runtime_summary({"attack_worker_total": 0, "errors": []})

    assert summary["agentic_security"] == {
        "action_total": 0,
        "authorization_decision_counts": {},
        "canary_event_total": 0,
        "canary_report": {},
        "amplification_metrics": {},
        "budget_stop_triggered": False,
        "untrusted_lineage_action_total": 0,
    }
