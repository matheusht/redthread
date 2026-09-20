"""Structured authorization audit logging and forensic event records."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from redthread.orchestration.models import (
    ActionEnvelope,
    AuthorizationDecision,
    AuthorizationDecisionType,
)


class AuthorizationAuditRecord(BaseModel):
    """Immutable forensic event record capturing an authorization decision."""

    model_config = ConfigDict(frozen=True)

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    action_hash: str
    actor_role: str
    capability: str
    target_sensitivity: str
    decision: AuthorizationDecisionType
    policy_id: str
    reason: str
    reason_code: str | None = None
    matched_rules: list[str] = Field(default_factory=list)
    required_escalation: bool = False


def compute_action_hash(action: ActionEnvelope) -> str:
    """Compute deterministic SHA-256 fingerprint for an ActionEnvelope."""
    payload = {
        "actor_id": action.actor_id,
        "actor_role": action.actor_role,
        "capability": action.capability,
        "target_sensitivity": action.target_sensitivity,
        "arguments": action.arguments,
        "trust_level": action.provenance.trust_level.value,
        "origin_id": action.provenance.origin_id,
    }
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class AuditLogger:
    """In-memory bounded audit log for authorization events."""

    def __init__(self, max_records: int = 1000) -> None:
        self.max_records = max_records
        self._records: list[AuthorizationAuditRecord] = []

    def record(
        self, action: ActionEnvelope, decision: AuthorizationDecision
    ) -> AuthorizationAuditRecord:
        entry = AuthorizationAuditRecord(
            action_hash=compute_action_hash(action),
            actor_role=action.actor_role,
            capability=action.capability,
            target_sensitivity=action.target_sensitivity,
            decision=decision.decision,
            policy_id=decision.policy_id,
            reason=decision.reason,
            reason_code=decision.reason_code,
            matched_rules=list(decision.matched_rules),
            required_escalation=decision.required_escalation,
        )
        self._records.append(entry)
        if len(self._records) > self.max_records:
            self._records = self._records[-self.max_records:]
        return entry

    def get_records(self) -> list[AuthorizationAuditRecord]:
        return list(self._records)

    def clear(self) -> None:
        self._records.clear()
