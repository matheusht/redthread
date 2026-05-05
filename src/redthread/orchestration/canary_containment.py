"""Live canary containment guard for production execution boundaries."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

_CANARY_RE = re.compile(r"\bCANARY_[A-Z0-9_]+\b")
_EXECUTION_BOUNDARY_SEAMS = {
    "attack.target",
    "controlled.live_adapter",
    "defense.replay",
    "sandbox.replay",
    "strategy.static_seed_replay",
    "telemetry.canary",
    "tool.attack",
}
_ANALYSIS_ONLY_SEAMS = {
    "judge.autocot",
    "judge.score",
}


class CanaryContainmentDecisionType(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    ESCALATE = "escalate"


class CanaryBoundaryKind(str, Enum):
    ANALYSIS_ONLY = "analysis_only"
    SHARED_STATE = "shared_state"
    MEMORY_WRITE = "memory_write"
    EXECUTION_BOUNDARY = "execution_boundary"
    UNKNOWN = "unknown"


class CanaryContainmentDecision(BaseModel):
    decision: CanaryContainmentDecisionType
    seam: str
    boundary: CanaryBoundaryKind
    canary_tags: list[str] = Field(default_factory=list)
    blocked_point: str | None = None
    reason: str

    @property
    def blocked(self) -> bool:
        return self.decision == CanaryContainmentDecisionType.BLOCK


def extract_canary_tags(*values: Any) -> list[str]:
    """Extract stable canary tags from strings, lists, and nested metadata."""
    tags: list[str] = []

    def add(tag: str) -> None:
        if tag.startswith("CANARY_") and tag not in tags:
            tags.append(tag)

    def walk(value: Any) -> None:
        if value is None:
            return
        if isinstance(value, str):
            for match in _CANARY_RE.findall(value):
                add(match)
            return
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
            return
        if isinstance(value, (list, tuple, set)):
            for item in value:
                walk(item)

    for value in values:
        walk(value)
    return tags


def classify_canary_boundary(seam: str) -> CanaryBoundaryKind:
    if seam in _ANALYSIS_ONLY_SEAMS or seam.startswith("judge."):
        return CanaryBoundaryKind.ANALYSIS_ONLY
    if seam in _EXECUTION_BOUNDARY_SEAMS or seam.endswith(".target") or seam.startswith("tool."):
        return CanaryBoundaryKind.EXECUTION_BOUNDARY
    if "memory" in seam:
        return CanaryBoundaryKind.MEMORY_WRITE
    if "state" in seam or "summary" in seam:
        return CanaryBoundaryKind.SHARED_STATE
    return CanaryBoundaryKind.UNKNOWN


def evaluate_canary_containment(
    *,
    seam: str,
    prompt: str = "",
    metadata: dict[str, Any] | None = None,
    canary_tags: list[str] | None = None,
    mode: str = "block_execution_boundary",
) -> CanaryContainmentDecision:
    """Return the live containment decision for one pending boundary crossing."""
    tags = extract_canary_tags(prompt, metadata, canary_tags or [])
    boundary = classify_canary_boundary(seam)
    if not tags:
        return CanaryContainmentDecision(
            decision=CanaryContainmentDecisionType.ALLOW,
            seam=seam,
            boundary=boundary,
            reason="no canary tags present",
        )
    if boundary == CanaryBoundaryKind.ANALYSIS_ONLY:
        return CanaryContainmentDecision(
            decision=CanaryContainmentDecisionType.ALLOW,
            seam=seam,
            boundary=boundary,
            canary_tags=tags,
            reason="analysis-only boundary allows tagged evidence",
        )
    if mode in {"monitor_only", "off"}:
        return CanaryContainmentDecision(
            decision=CanaryContainmentDecisionType.ALLOW,
            seam=seam,
            boundary=boundary,
            canary_tags=tags,
            reason="monitor-only canary policy",
        )
    if boundary in {CanaryBoundaryKind.EXECUTION_BOUNDARY, CanaryBoundaryKind.MEMORY_WRITE}:
        return CanaryContainmentDecision(
            decision=CanaryContainmentDecisionType.BLOCK,
            seam=seam,
            boundary=boundary,
            canary_tags=tags,
            blocked_point=seam,
            reason="canary-tagged content reached a protected boundary",
        )
    return CanaryContainmentDecision(
        decision=CanaryContainmentDecisionType.ALLOW,
        seam=seam,
        boundary=boundary,
        canary_tags=tags,
        reason="non-execution boundary recorded",
    )
