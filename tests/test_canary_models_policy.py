from __future__ import annotations

from redthread.config.settings import CanaryPolicyPreset, RedThreadSettings
from redthread.orchestration.canary_containment import (
    CanaryContainmentDecisionType,
    evaluate_canary_containment,
)
from redthread.orchestration.canary_flow import (
    CanaryPropagationReport,
    CanaryStageEvent,
    build_typed_canary_report,
    record_canary_stage,
)
from redthread.orchestration.runtime_summary import merge_canary_reports
from redthread.orchestration.supervisor import _worker_canary_update


def test_canary_flow_uses_typed_stage_and_report_models() -> None:
    stage = CanaryStageEvent.model_validate(
        record_canary_stage("execution_plan", ["CANARY_EXT_TOOL_01"], blocked=True)
    )
    report = build_typed_canary_report([stage])

    assert isinstance(report, CanaryPropagationReport)
    assert report.first_blocked_point == "execution_plan"
    assert report.reached_execution_boundary is True
    assert report.contained is True


def test_canary_policy_presets_are_explicit_settings() -> None:
    settings = RedThreadSettings(canary_policy_preset="monitor_only")

    assert settings.canary_policy_preset == CanaryPolicyPreset.MONITOR_ONLY


def test_block_execution_boundary_preset_allows_memory_boundary() -> None:
    decision = evaluate_canary_containment(
        seam="memory.write",
        prompt="store CANARY_EXT_TOOL_01",
        mode=CanaryPolicyPreset.BLOCK_EXECUTION_BOUNDARY,
    )

    assert decision.decision == CanaryContainmentDecisionType.ALLOW
    assert decision.boundary == "memory_write"


def test_strict_fail_closed_blocks_shared_state_boundary() -> None:
    decision = evaluate_canary_containment(
        seam="supervisor.state",
        prompt="state CANARY_EXT_TOOL_01",
        mode=CanaryPolicyPreset.STRICT_FAIL_CLOSED,
    )

    assert decision.decision == CanaryContainmentDecisionType.BLOCK
    assert decision.blocked_point == "supervisor.state"


def test_supervisor_worker_canary_update_merges_worker_reports() -> None:
    existing = build_typed_canary_report([
        CanaryStageEvent(stage="shared_state", canary_tags=["CANARY_EXT_TOOL_01"])
    ]).model_dump(mode="json")
    report = build_typed_canary_report([
        CanaryStageEvent(stage="tool_execution", canary_tags=["CANARY_EXT_TOOL_01"], blocked=True)
    ]).model_dump(mode="json")

    update = _worker_canary_update([{"live_canary_report": report}], existing)

    assert update["live_canary_event_total"] == 2
    assert update["live_canary_report"]["crossed_boundaries"] == ["shared_state", "tool_execution"]
    assert update["live_canary_report"]["first_blocked_point"] == "tool_execution"


def test_merge_canary_reports_preserves_uncontained_failure() -> None:
    merged = merge_canary_reports([
        {
            "injection_point": "tool_return",
            "crossed_boundaries": ["tool_execution"],
            "stage_count": 1,
            "reached_execution_boundary": True,
            "contained": False,
        }
    ])

    assert merged["reached_execution_boundary"] is True
    assert merged["contained"] is False
