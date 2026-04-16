"""Canary propagation reporting for Phase 8D."""

from __future__ import annotations

from typing import Any


def record_canary_stage(stage: str, canary_tags: list[str]) -> dict[str, Any]:
    return {"stage": stage, "canary_tags": canary_tags}


def build_canary_report(stages: list[dict[str, Any]]) -> dict[str, Any]:
    non_empty = [stage for stage in stages if stage.get("canary_tags")]
    crossed = [stage["stage"] for stage in non_empty]
    execution_boundary = any(stage in {"execution_plan", "outbound_request", "tool_execution"} for stage in crossed)
    return {
        "injection_point": crossed[0] if crossed else None,
        "crossed_boundaries": crossed,
        "stage_count": len(crossed),
        "reached_execution_boundary": execution_boundary,
        "contained": bool(crossed) and not execution_boundary,
    }
