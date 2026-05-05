"""Canary propagation reporting for Phase 8D."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, Field

_EXECUTION_STAGES = {"execution_plan", "outbound_request", "tool_execution"}


class CanaryStageEvent(BaseModel):
    """Typed event for one canary boundary crossing."""

    stage: str
    canary_tags: list[str] = Field(default_factory=list)
    blocked: bool = False


class CanaryPropagationReport(BaseModel):
    """Typed summary of canary propagation across runtime boundaries."""

    injection_point: str | None = None
    crossed_boundaries: list[str] = Field(default_factory=list)
    stage_count: int = 0
    first_blocked_point: str | None = None
    reached_execution_boundary: bool = False
    contained: bool = False


def record_canary_stage(stage: str, canary_tags: list[str], *, blocked: bool = False) -> dict[str, Any]:
    return CanaryStageEvent(stage=stage, canary_tags=canary_tags, blocked=blocked).model_dump(mode="json")


def build_typed_canary_report(stages: Sequence[dict[str, Any] | CanaryStageEvent]) -> CanaryPropagationReport:
    events = [CanaryStageEvent.model_validate(stage) for stage in stages]
    non_empty = [event for event in events if event.canary_tags]
    crossed = [event.stage for event in non_empty]
    execution_boundary = any(stage in _EXECUTION_STAGES for stage in crossed)
    blocked = [event for event in non_empty if event.blocked]
    first_blocked = blocked[0].stage if blocked else None
    return CanaryPropagationReport(
        injection_point=crossed[0] if crossed else None,
        crossed_boundaries=crossed,
        stage_count=len(crossed),
        first_blocked_point=first_blocked,
        reached_execution_boundary=execution_boundary,
        contained=bool(crossed) and (bool(first_blocked) or not execution_boundary),
    )


def build_canary_report(stages: list[dict[str, Any]]) -> dict[str, Any]:
    return build_typed_canary_report(stages).model_dump(mode="json")
