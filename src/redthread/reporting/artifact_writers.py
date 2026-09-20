"""Helper builders and row formatters for operator artifact reporting."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from redthread.models import AttackResult, CampaignResult
from redthread.orchestration.models import CampaignPlan
from redthread.reporting.models import (
    FindingReport,
    JudgeVerdictSummary,
    ScopeSummary,
)


def build_scope_summary(campaign: CampaignResult, plan: CampaignPlan | None) -> ScopeSummary:
    """Derive scope summary from explicit CampaignPlan or inferred trace metadata."""
    if plan is not None:
        return ScopeSummary(
            target_ids=plan.scope.target_ids,
            allowed_tools=plan.scope.allowed_tools,
            denied_tools=plan.scope.denied_tools,
            allowed_domains=plan.scope.allowed_domains,
        )
    target_ids = sorted(
        {item for result in campaign.results for item in metadata_list(result, "scope_target_ids")}
    )
    return ScopeSummary(
        target_ids=target_ids,
        limitations=["scope summary inferred from campaign traces because no CampaignPlan was supplied"],
    )


def collect_risk_ids(campaign: CampaignResult, plan: CampaignPlan | None) -> list[str]:
    """Collect tested risk plugin IDs."""
    if plan is not None:
        return plan.risk_ids
    return sorted({str(result.trace.metadata.get("risk_plugin_id", "unknown")) for result in campaign.results})


def collect_strategy_ids(campaign: CampaignResult, plan: CampaignPlan | None) -> list[str]:
    """Collect tested strategy IDs."""
    if plan is not None:
        return plan.strategy_ids
    return sorted({str(result.trace.metadata.get("strategy_id", result.trace.algorithm)) for result in campaign.results})


def build_finding_report(
    result: AttackResult,
    regression_links: list[dict[str, Any]],
    defense_status_by_trace_id: Mapping[str, str],
) -> FindingReport:
    """Format an individual confirmed finding report."""
    link = link_for_result(result, regression_links)
    return FindingReport(
        finding_id=result.id,
        trace_id=result.trace.id,
        risk_plugin_id=str(result.trace.metadata.get("risk_plugin_id", "unknown")),
        strategy_id=str(result.trace.metadata.get("strategy_id", result.trace.algorithm)),
        severity=severity_from_score(result.verdict.score),
        judge_score=result.verdict.score,
        judge_verdict="confirmed_jailbreak",
        detector_hint_summary=metadata_dict(result, "detector_hint_summary"),
        defense_status=defense_status_by_trace_id.get(result.trace.id, "not_reported"),
        regression_case_id=str(link.get("regression_case_id", "")) if link else "",
        regression_status=str(link.get("status", "not_created")) if link else "not_created",
    )


def build_judge_verdict_summary(result: AttackResult) -> JudgeVerdictSummary:
    """Format single judge verdict summary row."""
    return JudgeVerdictSummary(
        result_id=result.id,
        trace_id=result.trace.id,
        judge_score=result.verdict.score,
        is_jailbreak=result.verdict.is_jailbreak,
        rubric_name=result.verdict.rubric_name,
        reasoning=result.verdict.reasoning,
    )


def metadata_list(result: AttackResult, key: str) -> list[str]:
    raw = result.trace.metadata.get(key, [])
    return [str(item) for item in raw] if isinstance(raw, list) else []


def metadata_dict(result: AttackResult, key: str) -> dict[str, Any]:
    raw = result.trace.metadata.get(key, {})
    return dict(raw) if isinstance(raw, Mapping) else {}


def link_for_result(result: AttackResult, links: list[dict[str, Any]]) -> dict[str, Any]:
    for link in links:
        if link.get("source_finding_id") == result.id or link.get("source_trace_id") == result.trace.id:
            return link
    return {}


def build_report_limitations(scope: ScopeSummary) -> list[str]:
    return [
        "Detector hints are weak static signals only; JudgeAgent verdicts own findings.",
        "Evidence mode must not be treated as broader live enforcement proof.",
        *scope.limitations,
    ]


def build_pr_checklist_items(findings: list[FindingReport]) -> list[str]:
    items = ["Review report scope and evidence limitations before promotion."]
    if findings:
        items.append("Confirm every JudgeAgent finding has an owner and mitigation plan.")
        items.append("Add or link regression cases for confirmed findings before closing the PR.")
    else:
        items.append("Confirm no new findings were introduced by this change.")
    return items


def build_stakeholder_summary(campaign: CampaignResult, finding_count: int) -> str:
    return f"RedThread found {finding_count} confirmed finding(s) across {len(campaign.results)} run(s)."


def severity_from_score(score: float) -> str:
    if score >= 4.5:
        return "critical"
    if score >= 3.5:
        return "high"
    return "medium" if score >= 2.5 else "low"
