"""Tests for structured authorization audit logging and forensic event tracking."""

from __future__ import annotations

from redthread.orchestration.models import (
    ActionEffect,
    ActionEnvelope,
    AuthorizationDecisionType,
    ProvenanceRecord,
    ProvenanceSourceKind,
    TrustLevel,
)
from redthread.tools.authorization.audit import (
    AuditLogger,
    AuthorizationAuditRecord,
    compute_action_hash,
)
from redthread.tools.authorization.engine import AuthorizationEngine
from redthread.tools.authorization.presets import (
    FS_READ_ONLY_PRESET,
    default_least_agency_policies,
)


def _make_action(
    actor_id: str = "preset-test",
    actor_role: str = "filesystem_reader",
    capability: str = "file.read",
    trust_level: TrustLevel = TrustLevel.TRUSTED,
    sensitivity: str = "low",
    args: dict | None = None,
) -> ActionEnvelope:
    provenance = ProvenanceRecord(
        source_kind=ProvenanceSourceKind.INTERNAL_AGENT,
        trust_level=trust_level,
        origin_id=actor_id,
        derived_from_untrusted=(trust_level == TrustLevel.UNTRUSTED),
    )
    return ActionEnvelope(
        actor_id=actor_id,
        actor_role=actor_role,
        capability=capability,
        tool_name=capability,
        arguments=args if args is not None else {"path": "/workspace/safe/readme"},
        target_sensitivity=sensitivity,
        provenance=provenance,
        requested_effect=ActionEffect.READ,
    )


def test_audit_records_captured_on_authorize() -> None:
    engine = AuthorizationEngine(default_least_agency_policies())
    assert engine.get_audit_records() == []

    action = _make_action()
    decision = engine.authorize(action)
    assert decision.decision == AuthorizationDecisionType.ALLOW

    records = engine.get_audit_records()
    assert len(records) == 1
    rec = records[0]
    assert isinstance(rec, AuthorizationAuditRecord)
    assert rec.actor_role == "filesystem_reader"
    assert rec.capability == "file.read"
    assert rec.decision == AuthorizationDecisionType.ALLOW
    assert rec.policy_id == "fs-read-only"
    assert rec.action_hash == compute_action_hash(action)
    assert rec.timestamp


def test_audit_records_denied_decision_forensics() -> None:
    engine = AuthorizationEngine([FS_READ_ONLY_PRESET])
    out_of_bounds = _make_action(
        actor_id="bad-actor",
        actor_role="filesystem_reader",
        capability="file.read",
        args={"path": "/etc/passwd"},
    )
    decision = engine.authorize(out_of_bounds)
    assert decision.decision == AuthorizationDecisionType.DENY

    records = engine.get_audit_records()
    assert len(records) == 1
    rec = records[0]
    assert rec.decision == AuthorizationDecisionType.DENY
    assert "scope_boundary" in rec.matched_rules
    assert rec.policy_id == "scope-boundary"
    assert rec.actor_role == "filesystem_reader"


def test_audit_logger_ring_buffer_eviction() -> None:
    engine = AuthorizationEngine(default_least_agency_policies(), max_audit_records=3)

    for i in range(5):
        action = _make_action(actor_id=f"agent-{i}")
        engine.authorize(action)

    records = engine.get_audit_records()
    assert len(records) == 3
    # Most recent entries should be agent-2, agent-3, agent-4
    assert [r.action_hash for r in records] == [
        compute_action_hash(_make_action(actor_id=f"agent-{i}")) for i in range(2, 5)
    ]


def test_clear_audit_records() -> None:
    engine = AuthorizationEngine(default_least_agency_policies())
    engine.authorize(_make_action())
    assert len(engine.get_audit_records()) == 1

    engine.clear_audit_records()
    assert engine.get_audit_records() == []


def test_audit_logger_standalone() -> None:
    logger = AuditLogger(max_records=2)
    action = _make_action()
    engine = AuthorizationEngine(default_least_agency_policies())
    decision = engine.authorize(action)
    entry = logger.record(action, decision)
    assert entry.action_hash
    assert len(logger.get_records()) == 1
    logger.clear()
    assert logger.get_records() == []

