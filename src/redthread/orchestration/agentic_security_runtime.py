"""Additive agentic-security runtime review for supervisor flows."""

from __future__ import annotations

from typing import Any, cast

from redthread.models import CampaignConfig
from redthread.orchestration.canary_flow import build_canary_report, record_canary_stage
from redthread.orchestration.graphs.tool_attack_graph import run_tool_attack_scenario
from redthread.orchestration.models import ActionEnvelope, AmplificationMetrics
from redthread.orchestration.scenarios.confused_deputy import run_confused_deputy_scenario
from redthread.orchestration.scenarios.resource_amplification import (
    run_resource_amplification_scenario,
)
from redthread.telemetry.runtime_budgets import evaluate_runtime_budget
from redthread.tools.authorization import AuthorizationEngine, default_least_agency_policies
from redthread.tools.fixtures.agentic_security import poisoned_compliance_fixture

TOOL_KEYWORDS = ("tool", "mcp", "function", "shell", "db", "database", "api", "plugin")
DEPUTY_KEYWORDS = ("agent", "worker", "delegate", "handoff", "supervisor", "pipeline")
AMPLIFICATION_KEYWORDS = ("retry", "repair", "loop", "budget", "token", "fallback", "amplif")


def should_run_agentic_security_review(config: CampaignConfig) -> bool:
    text = f"{config.objective} {config.target_system_prompt}".lower()
    return any(keyword in text for keyword in TOOL_KEYWORDS + DEPUTY_KEYWORDS + AMPLIFICATION_KEYWORDS)


def run_agentic_security_review(config: CampaignConfig) -> dict[str, Any]:
    if not should_run_agentic_security_review(config):
        return {
            "enabled": False,
            "evidence_mode": "not_applicable",
            "scenario_reports": [],
            "action_total": 0,
            "authorization_decision_counts": {},
            "canary_event_total": 0,
            "canary_report": {},
            "amplification_metrics": {},
            "budget_stop_triggered": False,
            "untrusted_lineage_action_total": 0,
        }

    engine = AuthorizationEngine(default_least_agency_policies())
    reports: list[dict[str, Any]] = []
    decision_counts: dict[str, int] = {}
    action_total = 0
    canary_event_total = 0
    untrusted_lineage_action_total = 0
    canary_reports: list[dict[str, Any]] = []
    amplification_metrics: dict[str, Any] = {}
    budget_stop_triggered = False

    text = f"{config.objective} {config.target_system_prompt}".lower()

    if any(keyword in text for keyword in TOOL_KEYWORDS):
        tool_case = run_tool_attack_scenario(
            poisoned_compliance_fixture(),
            arguments={"tenant": "campaign-runtime", "report_type": "runtime-review"},
        )
        requested_action = cast(dict[str, Any], tool_case["requested_action"])
        tool_response = cast(dict[str, Any], tool_case["tool_response"])
        canary_tags = cast(list[str], tool_response["canary_tags"])
        action = ActionEnvelope.model_validate(requested_action)
        decision = engine.authorize(action)
        report = build_canary_report(
            [
                record_canary_stage("tool_return", canary_tags),
                record_canary_stage("shared_state", canary_tags),
            ]
        )
        reports.append({
            "scenario_id": "tool_poisoning_runtime_review",
            "threat": tool_case["threat"],
            "authorization_decision": decision.model_dump(mode="json"),
            "canary_report": report,
        })
        _count_decision(decision_counts, decision.decision.value)
        action_total += 1
        canary_event_total += len(canary_tags)
        untrusted_lineage_action_total += 1 if action.provenance.has_untrusted_lineage else 0
        canary_reports.append(report)

    if any(keyword in text for keyword in DEPUTY_KEYWORDS):
        deputy_case = run_confused_deputy_scenario()
        requested_action = cast(dict[str, Any], deputy_case["requested_action"])
        action = ActionEnvelope.model_validate(requested_action)
        decision = engine.authorize(action)
        reports.append({
            "scenario_id": "confused_deputy_runtime_review",
            "threats": deputy_case["threats"],
            "authorization_decision": decision.model_dump(mode="json"),
            "lineage_loss_detected": deputy_case["lineage_loss_detected"],
        })
        _count_decision(decision_counts, decision.decision.value)
        action_total += 1
        untrusted_lineage_action_total += 1 if action.provenance.has_untrusted_lineage else 0

    if any(keyword in text for keyword in AMPLIFICATION_KEYWORDS):
        amplification = run_resource_amplification_scenario(repair_loops=4)
        metrics = AmplificationMetrics.model_validate(amplification["amplification_metrics"])
        budget = evaluate_runtime_budget(metrics)
        reports.append({
            "scenario_id": "resource_amplification_runtime_review",
            "threat": amplification["threat"],
            "budget_decision": budget,
        })
        amplification_metrics = metrics.model_dump(mode="json")
        budget_stop_triggered = bool(budget["stop_triggered"])

    canary_report = _merge_canary_reports(canary_reports)
    return {
        "enabled": True,
        "evidence_mode": "sealed_runtime_review",
        "scenario_reports": reports,
        "action_total": action_total,
        "authorization_decision_counts": decision_counts,
        "canary_event_total": canary_event_total,
        "canary_report": canary_report,
        "amplification_metrics": amplification_metrics,
        "budget_stop_triggered": budget_stop_triggered,
        "untrusted_lineage_action_total": untrusted_lineage_action_total,
    }


def _count_decision(counts: dict[str, int], decision: str) -> None:
    counts[decision] = counts.get(decision, 0) + 1


def _merge_canary_reports(reports: list[dict[str, Any]]) -> dict[str, Any]:
    if not reports:
        return {}
    crossings: list[str] = []
    for report in reports:
        for boundary in report.get("crossed_boundaries", []):
            if boundary not in crossings:
                crossings.append(boundary)
    return {
        "injection_point": reports[0].get("injection_point"),
        "crossed_boundaries": crossings,
        "reached_execution_boundary": any(r.get("reached_execution_boundary") for r in reports),
        "contained": all(r.get("contained", False) for r in reports),
    }
