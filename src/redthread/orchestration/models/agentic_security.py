"""Agentic security schema for Phase 8A."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class AgenticSecurityThreat(str, Enum):
    TOOL_POISONING = "tool_poisoning"
    TOOL_LEAK = "tool_leak"
    CROSS_TOOL_CONTAMINATION = "cross_tool_contamination"
    CONFUSED_DEPUTY = "confused_deputy"
    PRIVILEGE_LAUNDERING = "privilege_laundering"
    RESOURCE_AMPLIFICATION = "resource_amplification"
    CANARY_PROPAGATION = "canary_propagation"
    DETERMINISTIC_CONTAINMENT = "deterministic_containment"


class ProvenanceSourceKind(str, Enum):
    USER = "user"
    EXTERNAL_TOOL = "external_tool"
    EXTERNAL_DOCUMENT = "external_document"
    INTERNAL_AGENT = "internal_agent"
    SYSTEM = "system"
    MEMORY = "memory"
    REPLAY_FIXTURE = "replay_fixture"


class TrustLevel(str, Enum):
    TRUSTED = "trusted"
    DERIVED = "derived"
    UNTRUSTED = "untrusted"


class BoundaryType(str, Enum):
    TOOL_RETURN = "tool_return"
    TOOL_SELECTION = "tool_selection"
    AGENT_HANDOFF = "agent_handoff"
    SHARED_STATE = "shared_state"
    MEMORY_WRITE = "memory_write"
    EXECUTION_PLAN = "execution_plan"
    OUTBOUND_REQUEST = "outbound_request"


class AuthorizationDecisionType(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ESCALATE = "escalate"


class ActionEffect(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    EXFILTRATE = "exfiltrate"
    DELEGATE = "delegate"


class BoundaryCrossing(BaseModel):
    boundary: BoundaryType
    entered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    detail: str = ""


class ProvenanceRecord(BaseModel):
    source_kind: ProvenanceSourceKind
    trust_level: TrustLevel
    origin_id: str
    parent_ids: list[str] = Field(default_factory=list)
    boundary_crossings: list[BoundaryCrossing] = Field(default_factory=list)
    canary_tags: list[str] = Field(default_factory=list)
    derived_from_untrusted: bool = False

    @model_validator(mode="after")
    def normalize_lineage_flags(self) -> "ProvenanceRecord":
        if self.trust_level == TrustLevel.TRUSTED:
            if self.derived_from_untrusted:
                msg = "trusted provenance cannot also be marked derived_from_untrusted"
                raise ValueError(msg)
            self.derived_from_untrusted = False
            return self
        self.derived_from_untrusted = True
        return self

    @property
    def crossed_boundary_count(self) -> int:
        return len(self.boundary_crossings)

    @property
    def has_untrusted_lineage(self) -> bool:
        return self.trust_level in {TrustLevel.DERIVED, TrustLevel.UNTRUSTED}


class AuthorizationDecision(BaseModel):
    decision: AuthorizationDecisionType
    policy_id: str
    reason: str
    matched_rules: list[str] = Field(default_factory=list)
    required_escalation: bool = False


class ActionEnvelope(BaseModel):
    action_id: str = Field(default_factory=lambda: f"action-{str(uuid4())[:8]}")
    actor_id: str
    actor_role: str
    capability: str
    tool_name: str
    arguments: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    target_sensitivity: str = "low"
    provenance: ProvenanceRecord
    requested_effect: ActionEffect
    authorization_status: AuthorizationDecisionType | None = None
    authorization_reason: str = ""
    requires_human_approval: bool = False
    canary_tags: list[str] = Field(default_factory=list)


class AmplificationMetrics(BaseModel):
    tool_call_count: int = 0
    retry_count: int = 0
    duplicate_call_count: int = 0
    loop_depth: int = 0
    fallback_count: int = 0
    token_growth_ratio: float = 1.0
    budget_breached: bool = False
