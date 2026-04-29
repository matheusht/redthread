"""Builders for guide-style RedThread operator artifacts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from redthread.models import AttackResult, CampaignResult
from redthread.orchestration.models import CampaignPlan
from redthread.reporting.hero_proof import build_hero_proof_bundle
from redthread.reporting.models import (
    DETECTOR_LIMITATION,
    FindingReport,
    JudgeVerdictSummary,
    OperatorArtifactBundle,
    PRChecklist,
    RegressionPackSummary,
    RulesOfEngagementSummary,
    ScopeSummary,
    SecurityCard,
    StakeholderReadout,
    VulnerabilityReport,
)
from redthread.reporting.persona_artifacts import persona_artifacts_from_metadata


def build_operator_artifact_bundle(
    campaign: CampaignResult,
    *,
    plan: CampaignPlan | None = None,
    regression_links: list[Mapping[str, Any]] | None = None,
    defense_status_by_trace_id: Mapping[str, str] | None = None,
) -> OperatorArtifactBundle:
    """Build guide-style operator artifacts without changing execution state."""
    links = [dict(link) for link in regression_links or []]
    scope = _scope_summary(campaign, plan)
    risks = _risk_ids(campaign, plan)
    strategies = _strategy_ids(campaign, plan)
    limitations = _report_limitations(scope)
    findings = [
        _finding_report(result, links, defense_status_by_trace_id or {})
        for result in campaign.results
        if result.verdict.is_jailbreak
    ]
    persona_artifacts = persona_artifacts_from_metadata(campaign.metadata)
    bundle = OperatorArtifactBundle(
        campaign_id=campaign.id,
        rules_of_engagement=RulesOfEngagementSummary(
            objective=campaign.config.objective,
            scope=scope,
            risks_tested=risks,
            strategies_used=strategies,
            limitations=limitations,
        ),
        vulnerability_report=VulnerabilityReport(
            finding_count=len(findings),
            findings=findings,
            judge_verdicts=[_judge_verdict_summary(result) for result in campaign.results],
        ),
        security_card=SecurityCard(
            target_system_prompt_present=bool(campaign.config.target_system_prompt.strip()),
            tested_risks=risks,
            tested_strategies=strategies,
            attack_success_rate=campaign.attack_success_rate,
            average_judge_score=campaign.average_score,
            evidence_limitations=limitations,
        ),
        pr_checklist=PRChecklist(items=_pr_checklist_items(findings)),
        stakeholder_readout=StakeholderReadout(
            summary=_stakeholder_summary(campaign, len(findings)),
            confirmed_findings=len(findings),
            total_runs=len(campaign.results),
            evidence_mode=str(campaign.metadata.get("runtime_mode", "unknown")),
        ),
        regression_pack_summary=RegressionPackSummary(case_count=len(links), links=links),
        limitations=limitations,
        persona_outcome_telemetry=persona_artifacts["persona_outcome_telemetry"],
        adaptive_persona_weighting_plan=persona_artifacts["adaptive_persona_weighting_plan"],
    )
    hero_proof = build_hero_proof_bundle(campaign, bundle)
    bundle.hero_proof = hero_proof.model_dump(mode="json")
    bundle.ci_regression = hero_proof.ci_regression
    return bundle


def _scope_summary(campaign: CampaignResult, plan: CampaignPlan | None) -> ScopeSummary:
    if plan is not None:
        return ScopeSummary(
            target_ids=plan.scope.target_ids,
            allowed_tools=plan.scope.allowed_tools,
            denied_tools=plan.scope.denied_tools,
            allowed_domains=plan.scope.allowed_domains,
        )
    target_ids = sorted({item for result in campaign.results for item in _metadata_list(result, "scope_target_ids")})
    return ScopeSummary(
        target_ids=target_ids,
        limitations=["scope summary inferred from campaign traces because no CampaignPlan was supplied"],
    )


def _risk_ids(campaign: CampaignResult, plan: CampaignPlan | None) -> list[str]:
    if plan is not None:
        return plan.risk_ids
    return sorted({str(result.trace.metadata.get("risk_plugin_id", "unknown")) for result in campaign.results})


def _strategy_ids(campaign: CampaignResult, plan: CampaignPlan | None) -> list[str]:
    if plan is not None:
        return plan.strategy_ids
    return sorted({str(result.trace.metadata.get("strategy_id", result.trace.algorithm)) for result in campaign.results})


def _finding_report(
    result: AttackResult,
    regression_links: list[dict[str, Any]],
    defense_status_by_trace_id: Mapping[str, str],
) -> FindingReport:
    link = _link_for_result(result, regression_links)
    return FindingReport(
        finding_id=result.id,
        trace_id=result.trace.id,
        risk_plugin_id=str(result.trace.metadata.get("risk_plugin_id", "unknown")),
        strategy_id=str(result.trace.metadata.get("strategy_id", result.trace.algorithm)),
        severity=_severity_from_score(result.verdict.score),
        judge_score=result.verdict.score,
        judge_verdict="confirmed_jailbreak",
        detector_hint_summary=_metadata_dict(result, "detector_hint_summary"),
        defense_status=defense_status_by_trace_id.get(result.trace.id, "not_reported"),
        regression_case_id=str(link.get("regression_case_id", "")) if link else "",
        regression_status=str(link.get("status", "not_created")) if link else "not_created",
    )


def _judge_verdict_summary(result: AttackResult) -> JudgeVerdictSummary:
    return JudgeVerdictSummary(
        result_id=result.id,
        trace_id=result.trace.id,
        judge_score=result.verdict.score,
        is_jailbreak=result.verdict.is_jailbreak,
        rubric_name=result.verdict.rubric_name,
        reasoning=result.verdict.reasoning,
    )


def _metadata_list(result: AttackResult, key: str) -> list[str]:
    raw = result.trace.metadata.get(key, [])
    return [str(item) for item in raw] if isinstance(raw, list) else []


def _metadata_dict(result: AttackResult, key: str) -> dict[str, Any]:
    raw = result.trace.metadata.get(key, {})
    return dict(raw) if isinstance(raw, Mapping) else {}


def _link_for_result(result: AttackResult, links: list[dict[str, Any]]) -> dict[str, Any]:
    for link in links:
        if link.get("source_finding_id") == result.id or link.get("source_trace_id") == result.trace.id:
            return link
    return {}


def _report_limitations(scope: ScopeSummary) -> list[str]:
    return [
        "Detector hints are weak static signals only; JudgeAgent verdicts own findings.",
        "Evidence mode must not be treated as broader live enforcement proof.",
        *scope.limitations,
    ]


def _pr_checklist_items(findings: list[FindingReport]) -> list[str]:
    items = ["Review report scope and evidence limitations before promotion."]
    if findings:
        items.extend([
            "Confirm every JudgeAgent finding has an owner and mitigation plan.",
            "Add or link regression cases for confirmed findings before closing the PR.",
        ])
    else:
        items.append("Confirm no new findings were introduced by this change.")
    return items


def _stakeholder_summary(campaign: CampaignResult, finding_count: int) -> str:
    return f"RedThread found {finding_count} confirmed finding(s) across {len(campaign.results)} run(s)."


def _severity_from_score(score: float) -> str:
    if score >= 4.5:
        return "critical"
    if score >= 3.5:
        return "high"
    if score >= 2.5:
        return "medium"
    return "low"


__all__ = ["DETECTOR_LIMITATION", "build_operator_artifact_bundle"]
