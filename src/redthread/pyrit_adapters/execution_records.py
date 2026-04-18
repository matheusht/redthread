from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from redthread.runtime_modes import LIVE_PROVIDER


@dataclass(frozen=True)
class ExecutionMetadata:
    """Caller-supplied labels for one live provider send."""

    seam: str
    role: str
    evidence_class: str
    runtime_mode: str = LIVE_PROVIDER
    conversation_id: str | None = None
    authorization_decision: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionRecord:
    """Normalized result record for one provider-backed send."""

    seam: str
    role: str
    evidence_class: str
    model_name: str
    conversation_id: str
    runtime_mode: str
    success: bool
    error: str | None = None
    authorization_decision: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


ExecutionRecorder = Callable[[ExecutionRecord], None]


def build_execution_record(
    *,
    model_name: str,
    conversation_id: str,
    execution_metadata: ExecutionMetadata,
    success: bool,
    error: str | None = None,
) -> ExecutionRecord:
    return ExecutionRecord(
        seam=execution_metadata.seam,
        role=execution_metadata.role,
        evidence_class=execution_metadata.evidence_class,
        model_name=model_name,
        conversation_id=conversation_id,
        runtime_mode=execution_metadata.runtime_mode,
        success=success,
        error=error,
        authorization_decision=execution_metadata.authorization_decision,
        metadata=dict(execution_metadata.metadata),
    )
