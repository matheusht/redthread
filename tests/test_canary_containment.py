from __future__ import annotations

from redthread.orchestration.canary_flow import build_canary_report, record_canary_stage
from redthread.orchestration.graphs.tool_attack_graph import run_tool_attack_scenario
from redthread.orchestration.models import AmplificationMetrics
from redthread.orchestration.runtime_summary import build_runtime_summary
from redthread.orchestration.scenarios.resource_amplification import (
    run_resource_amplification_scenario,
)
from redthread.telemetry.canaries import inject_canary, merge_canary_tags
from redthread.telemetry.runtime_budgets import evaluate_runtime_budget
from redthread.tools.fixtures.agentic_security import poisoned_compliance_fixture


def test_canary_helpers_merge_unique_tags() -> None:
    payload = inject_canary("SOC2 review required", "CANARY_EXT_TOOL_01")
    merged = merge_canary_tags(payload["canary_tags"], ["CANARY_EXT_TOOL_01", "CANARY_SUMMARY_02"])

    assert payload["canary_tags"] == ["CANARY_EXT_TOOL_01"]
    assert merged == ["CANARY_EXT_TOOL_01", "CANARY_SUMMARY_02"]


def test_canary_report_detects_execution_boundary_crossing() -> None:
    result = run_tool_attack_scenario(
        poisoned_compliance_fixture(),
        arguments={"tenant": "acme-prod", "report_type": "soc2"},
    )
    tags = result["tool_response"]["canary_tags"]

    report = build_canary_report(
        [
            record_canary_stage("tool_return", tags),
            record_canary_stage("shared_state", tags),
            record_canary_stage("execution_plan", tags),
        ]
    )

    assert report["injection_point"] == "tool_return"
    assert report["reached_execution_boundary"] is True
    assert report["contained"] is False


def test_runtime_budget_stops_resource_amplification_case() -> None:
    result = run_resource_amplification_scenario(repair_loops=4)
    metrics = AmplificationMetrics.model_validate(result["amplification_metrics"])

    decision = evaluate_runtime_budget(metrics)

    assert decision["stop_triggered"] is True
    assert "retry_count" in decision["breaches"]


def test_runtime_summary_surfaces_canary_and_budget_fields() -> None:
    summary = build_runtime_summary(
        {
            "errors": [],
            "canary_event_total": 2,
            "canary_report": {"reached_execution_boundary": True},
            "budget_stop_triggered": True,
            "amplification_metrics": {"budget_breached": True},
        }
    )

    assert summary["agentic_security"]["canary_event_total"] == 2
    assert summary["agentic_security"]["canary_report"]["reached_execution_boundary"] is True
    assert summary["agentic_security"]["budget_stop_triggered"] is True
