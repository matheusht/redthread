"""Pydantic models for guide-style RedThread operator artifacts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

DETECTOR_LIMITATION = "weak static signals only; not proof; JudgeAgent owns verdict"


class ScopeSummary(BaseModel):
    """Operator-readable campaign scope."""

    target_ids: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    denied_tools: list[str] = Field(default_factory=list)
    allowed_domains: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class JudgeVerdictSummary(BaseModel):
    """Compact JudgeAgent verdict for one attack result."""

    result_id: str
    trace_id: str
    judge_score: float
    is_jailbreak: bool
    rubric_name: str
    reasoning: str


class FindingReport(BaseModel):
    """Vulnerability report row backed by a JudgeAgent-confirmed finding."""

    finding_id: str
    trace_id: str
    risk_plugin_id: str
    strategy_id: str
    severity: str
    judge_score: float
    judge_verdict: str
    detector_hint_summary: dict[str, Any] = Field(default_factory=dict)
    detector_hint_limitations: str = DETECTOR_LIMITATION
    defense_status: str = "not_reported"
    regression_case_id: str = ""
    regression_status: str = "not_created"


class RulesOfEngagementSummary(BaseModel):
    """Rules of engagement summary for the run."""

    objective: str
    scope: ScopeSummary
    risks_tested: list[str]
    strategies_used: list[str]
    limitations: list[str]


class VulnerabilityReport(BaseModel):
    """Confirmed findings and all JudgeAgent verdicts."""

    finding_count: int
    findings: list[FindingReport]
    judge_verdicts: list[JudgeVerdictSummary]
    detector_hint_limitations: str = DETECTOR_LIMITATION


class SecurityCard(BaseModel):
    """Model/system security card summary."""

    target_system_prompt_present: bool
    tested_risks: list[str]
    tested_strategies: list[str]
    attack_success_rate: float
    average_judge_score: float
    evidence_limitations: list[str]


class PRChecklist(BaseModel):
    """Pull-request checklist generated from report evidence."""

    items: list[str]


class StakeholderReadout(BaseModel):
    """Short non-technical readout."""

    summary: str
    confirmed_findings: int
    total_runs: int
    evidence_mode: str


class RegressionPackSummary(BaseModel):
    """Regression case links created from confirmed findings."""

    case_count: int
    links: list[dict[str, Any]]


class OperatorArtifactBundle(BaseModel):
    """Stable bundle for guide-style operator artifacts."""

    schema_version: str = "redthread.operator_artifacts.v1"
    campaign_id: str
    rules_of_engagement: RulesOfEngagementSummary
    vulnerability_report: VulnerabilityReport
    security_card: SecurityCard
    pr_checklist: PRChecklist
    stakeholder_readout: StakeholderReadout
    regression_pack_summary: RegressionPackSummary
    limitations: list[str]
    hero_proof: dict[str, Any] = Field(default_factory=dict)
    ci_regression: dict[str, Any] = Field(default_factory=dict)
    persona_outcome_telemetry: dict[str, Any] = Field(default_factory=dict)
    adaptive_persona_weighting_plan: dict[str, Any] = Field(default_factory=dict)


class OperatorReportManifest(BaseModel):
    """Stable manifest for persisted operator report artifacts."""

    schema_version: str = "redthread.operator_report_manifest.v1"
    campaign_id: str
    artifact_dir: str
    markdown_report: str
    json_report: str
    hero_proof: str = ""
    ci_regression: str = ""
    persona_outcome_telemetry: str = ""
    adaptive_persona_weighting_plan: str = ""
    bridge_prep_notes: list[str] = Field(default_factory=list)
