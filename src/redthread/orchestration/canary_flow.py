"""Canary propagation reporting for Phase 8D."""

from __future__ import annotations

from typing import Any


def record_canary_stage(stage: str, canary_tags: list[str]) -> dict[str, Any]:
    return {"stage": stage, "canary_tags": canary_tags}


def build_canary_report(stages: list[dict[str, Any]]) -> dict[str, Any]:
    non_empty = [stage for stage in stages if stage.get("canary_tags")]
    crossed = [stage["stage"] for stage in non_empty]
    execution_boundary = any(stage in {"execution_plan", "outbound_request", "tool_execution"} for stage in crossed)
    blocked = [stage for stage in non_empty if stage.get("blocked")]
    first_blocked = blocked[0]["stage"] if blocked else None
    return {
        "injection_point": crossed[0] if crossed else None,
        "crossed_boundaries": crossed,
        "stage_count": len(crossed),
        "first_blocked_point": first_blocked,
        "reached_execution_boundary": execution_boundary,
        "contained": bool(crossed) and (bool(first_blocked) or not execution_boundary),
    }
