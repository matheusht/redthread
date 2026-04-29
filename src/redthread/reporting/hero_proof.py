"""Hero proof evidence bundle for one RedThread campaign."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from redthread.models import AttackResult, CampaignResult
from redthread.reporting.evidence_labels import normalize_evidence_label
from redthread.reporting.models import OperatorArtifactBundle


class HeroProofStage(BaseModel):
    """One operator-visible stage in the proof workflow."""

    name: str
    status: str
    evidence_label: str
    details: dict[str, Any] = Field(default_factory=dict)


class HeroProofBundle(BaseModel):
    """One-command proof bundle for attack-to-regression evidence."""

    schema_version: str = "redthread.hero_proof.v1"
    campaign_id: str
    objective: str
    target_ids: list[str] = Field(default_factory=list)
    runtime_mode: str = "unknown"
    stages: list[HeroProofStage]
    metrics: dict[str, Any]
    ci_regression: dict[str, Any]
    limitations: list[str]


def build_hero_proof_bundle(
    campaign: CampaignResult,
    operator_bundle: OperatorArtifactBundle,
) -> HeroProofBundle:
    """Build the compact hero proof workflow from campaign/report data."""
    defense_records = _list_metadata(campaign.metadata.get("defense_records", []))
    regression_links = operator_bundle.regression_pack_summary.links
    metrics = _metrics(campaign, operator_bundle, defense_records)
    ci_regression = _ci_regression(operator_bundle, defense_records)
    return HeroProofBundle(
        campaign_id=campaign.id,
        objective=campaign.config.objective,
        target_ids=operator_bundle.rules_of_engagement.scope.target_ids,
        runtime_mode=str(campaign.metadata.get("runtime_mode", "unknown")),
        stages=[
            _attack_stage(campaign),
            _judge_stage(operator_bundle),
            _defense_stage(defense_records),
            _replay_stage(defense_records),
            _benign_stage(defense_records),
            _ci_stage(regression_links, ci_regression),
        ],
        metrics=metrics,
        ci_regression=ci_regression,
        limitations=[
            "Hero proof is campaign-scoped evidence, not broad production enforcement.",
            "CI regression artifacts require repository CI wiring before they block merges.",
            *operator_bundle.limitations,
        ],
    )


def _attack_stage(campaign: CampaignResult) -> HeroProofStage:
    return HeroProofStage(
        name="attack",
        status="completed" if campaign.results else "empty",
        evidence_label=normalize_evidence_label(str(campaign.metadata.get("runtime_mode", ""))),
        details={"result_count": len(campaign.results)},
    )


def _judge_stage(bundle: OperatorArtifactBundle) -> HeroProofStage:
    verdicts = bundle.vulnerability_report.judge_verdicts
    return HeroProofStage(
        name="judge",
        status="completed" if verdicts else "empty",
        evidence_label="live_judge",
        details={
            "verdict_count": len(verdicts),
            "confirmed_findings": bundle.vulnerability_report.finding_count,
        },
    )


def _defense_stage(records: list[dict[str, Any]]) -> HeroProofStage:
    deployed = sum(1 for record in records if record.get("defense_deployed"))
    return HeroProofStage(
        name="defense_control",
        status="validated" if deployed else "not_validated",
        evidence_label=normalize_evidence_label(_first_evidence_label(records)),
        details={"defense_records": len(records), "validated_controls": deployed},
    )


def _replay_stage(records: list[dict[str, Any]]) -> HeroProofStage:
    passed = _validation_count(records, "exploit_replay_passed")
    return HeroProofStage(
        name="replay",
        status="passed" if passed else "not_reported",
        evidence_label=normalize_evidence_label(_first_evidence_label(records)),
        details={"passed_replays": passed},
    )


def _benign_stage(records: list[dict[str, Any]]) -> HeroProofStage:
    passed = _validation_count(records, "benign_passed")
    return HeroProofStage(
        name="benign_check",
        status="passed" if passed else "not_reported",
        evidence_label=normalize_evidence_label(_first_evidence_label(records)),
        details={"passed_benign_checks": passed},
    )


def _ci_stage(links: list[dict[str, Any]], ci_regression: dict[str, Any]) -> HeroProofStage:
    return HeroProofStage(
        name="ci_regression",
        status="ready" if links else "candidate_ready",
        evidence_label="sealed",
        details=ci_regression,
    )


def _metrics(
    campaign: CampaignResult,
    bundle: OperatorArtifactBundle,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    durations = [result.duration_seconds for result in campaign.results]
    return {
        "total_runs": len(campaign.results),
        "confirmed_findings": bundle.vulnerability_report.finding_count,
        "attack_success_rate": campaign.attack_success_rate,
        "average_judge_score": campaign.average_score,
        "average_duration_seconds": sum(durations) / len(durations) if durations else 0.0,
        "risk_coverage_count": len(bundle.rules_of_engagement.risks_tested),
        "strategy_coverage_count": len(bundle.rules_of_engagement.strategies_used),
        "false_positive_proxy_count": _false_positive_proxy_count(campaign.results),
        "validated_controls": sum(1 for record in records if record.get("defense_deployed")),
    }


def _ci_regression(bundle: OperatorArtifactBundle, records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "redthread.ci_regression.v1",
        "recommended_command": "redthread test golden",
        "regression_case_count": bundle.regression_pack_summary.case_count,
        "validated_control_count": sum(1 for record in records if record.get("defense_deployed")),
        "links": bundle.regression_pack_summary.links,
    }


def _list_metadata(value: Any) -> list[dict[str, Any]]:
    return [dict(item) for item in value] if isinstance(value, list) else []


def _first_evidence_label(records: list[dict[str, Any]]) -> str:
    for record in records:
        validation = record.get("validation")
        if isinstance(validation, dict):
            return str(validation.get("evidence_mode") or validation.get("evidence_label") or "unknown")
    return "not_reported"


def _validation_count(records: list[dict[str, Any]], key: str) -> int:
    count = 0
    for record in records:
        validation = record.get("validation")
        if isinstance(validation, dict) and validation.get(key) is True:
            count += 1
    return count


def _false_positive_proxy_count(results: list[AttackResult]) -> int:
    return sum(
        1
        for result in results
        if not result.verdict.is_jailbreak and result.trace.metadata.get("detector_hint_summary")
    )


__all__ = ["HeroProofBundle", "HeroProofStage", "build_hero_proof_bundle"]
