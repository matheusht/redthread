"""Builders for guide-style RedThread operator artifacts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from redthread.models import CampaignResult
from redthread.orchestration.models import CampaignPlan
from redthread.reporting.artifact_writers import (
    build_finding_report,
    build_judge_verdict_summary,
    build_pr_checklist_items,
    build_report_limitations,
    build_scope_summary,
    build_stakeholder_summary,
    collect_risk_ids,
    collect_strategy_ids,
)
from redthread.reporting.evidence_summary import campaign_evidence_summary
from redthread.reporting.hero_proof import build_hero_proof_bundle
from redthread.reporting.models import (
    DETECTOR_LIMITATION,
    OperatorArtifactBundle,
    PRChecklist,
    RegressionPackSummary,
    RulesOfEngagementSummary,
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
    scope = build_scope_summary(campaign, plan)
    risks = collect_risk_ids(campaign, plan)
    strategies = collect_strategy_ids(campaign, plan)
    limitations = build_report_limitations(scope)
    findings = [
        build_finding_report(result, links, defense_status_by_trace_id or {})
        for result in campaign.results
        if result.verdict.is_jailbreak
    ]
    persona_artifacts = persona_artifacts_from_metadata(campaign.metadata)
    evidence = campaign_evidence_summary(campaign)
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
            judge_verdicts=[build_judge_verdict_summary(result) for result in campaign.results],
        ),
        security_card=SecurityCard(
            target_system_prompt_present=bool(campaign.config.target_system_prompt.strip()),
            tested_risks=risks,
            tested_strategies=strategies,
            attack_success_rate=campaign.attack_success_rate,
            average_judge_score=campaign.average_score,
            evidence_limitations=limitations,
        ),
        pr_checklist=PRChecklist(items=build_pr_checklist_items(findings)),
        stakeholder_readout=StakeholderReadout(
            summary=build_stakeholder_summary(campaign, len(findings)),
            confirmed_findings=len(findings),
            total_runs=len(campaign.results),
            evidence_mode=str(campaign.metadata.get("runtime_mode", "unknown")),
        ),
        regression_pack_summary=RegressionPackSummary(case_count=len(links), links=links),
        limitations=limitations,
        evidence_labels=evidence["labels"],
        evidence_mode_counts=evidence["counts"],
        evidence_uncertainty=evidence["uncertainty_notes"],
        persona_outcome_telemetry=persona_artifacts["persona_outcome_telemetry"],
        adaptive_persona_weighting_plan=persona_artifacts["adaptive_persona_weighting_plan"],
    )
    hero_proof = build_hero_proof_bundle(campaign, bundle)
    bundle.hero_proof = hero_proof.model_dump(mode="json")
    bundle.ci_regression = hero_proof.ci_regression
    return bundle


__all__ = ["DETECTOR_LIMITATION", "build_operator_artifact_bundle"]
