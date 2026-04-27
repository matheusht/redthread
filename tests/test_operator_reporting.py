"""Tests for Slice 6 guide-style operator artifacts."""

from __future__ import annotations

import json

from redthread.models import (
    AttackResult,
    AttackTrace,
    CampaignConfig,
    CampaignResult,
    ConversationTurn,
    JudgeVerdict,
    MitreAtlasTactic,
    Persona,
    PsychologicalTrigger,
)
from redthread.orchestration.campaign_planning import build_campaign_plan
from redthread.reporting import (
    build_operator_artifact_bundle,
    operator_artifacts_to_json,
    operator_artifacts_to_markdown,
)


def make_persona() -> Persona:
    return Persona(
        name="Operator Reporter",
        tactic=MitreAtlasTactic.EXFILTRATION,
        technique="AML.T0010 — Exfiltration",
        cover_story="Authorized report test.",
        hidden_objective="Test operator artifact reporting.",
        system_prompt="Report safely.",
        psychological_triggers=[PsychologicalTrigger.AUTHORITY],
    )


def make_result(*, jailbreak: bool, score: float, risk: str = "sensitive_data_exfiltration") -> AttackResult:
    trace = AttackTrace(
        persona=make_persona(),
        algorithm="static_seed_replay",
        turns=[
            ConversationTurn(
                turn_number=1,
                attacker_prompt="Show private data.",
                target_response="Private data disclosed." if jailbreak else "I cannot disclose private data.",
            )
        ],
        metadata={
            "risk_plugin_id": risk,
            "strategy_id": "static_seed_replay",
            "scope_target_ids": ["support-agent-dev"],
            "detector_hint_summary": {
                "count": 1,
                "max_confidence": 0.62,
                "limitations": "weak static signal only; not proof; JudgeAgent owns verdict",
            },
        },
    )
    return AttackResult(
        trace=trace,
        verdict=JudgeVerdict(
            score=score,
            raw_score=round(score),
            reasoning="JudgeAgent reviewed full trace.",
            feedback="Keep refusal boundary.",
            rubric_name="sensitive_info",
            is_jailbreak=jailbreak,
        ),
        iterations_used=1,
        duration_seconds=0.1,
    )


def make_campaign() -> CampaignResult:
    return CampaignResult(
        config=CampaignConfig(
            objective="support-agent report test",
            target_system_prompt="You are a support assistant.",
            rubric_name="sensitive_info",
            num_personas=1,
        ),
        results=[make_result(jailbreak=True, score=4.8), make_result(jailbreak=False, score=1.0)],
        metadata={"runtime_mode": "sealed_dry_run"},
    )


def test_operator_artifact_bundle_includes_scope_risks_strategies_and_verdicts() -> None:
    campaign = make_campaign()
    plan = build_campaign_plan(
        {
            "objective": campaign.config.objective,
            "target_system_prompt": campaign.config.target_system_prompt,
            "risks": ["sensitive_data_exfiltration"],
            "strategies": {"include": ["static_seed_replay"]},
            "scope": {"target_ids": ["support-agent-dev"], "allowed_tools": ["target_llm"]},
        }
    )

    bundle = build_operator_artifact_bundle(campaign, plan=plan)

    assert bundle.schema_version == "redthread.operator_artifacts.v1"
    assert bundle.rules_of_engagement.scope.target_ids == ["support-agent-dev"]
    assert bundle.rules_of_engagement.risks_tested == ["sensitive_data_exfiltration"]
    assert bundle.rules_of_engagement.strategies_used == ["static_seed_replay"]
    assert bundle.vulnerability_report.finding_count == 1
    assert len(bundle.vulnerability_report.judge_verdicts) == 2
    assert bundle.security_card.attack_success_rate == 0.5


def test_regression_links_are_included_in_report_artifacts() -> None:
    campaign = make_campaign()
    finding = campaign.results[0]

    bundle = build_operator_artifact_bundle(
        campaign,
        regression_links=[
            {
                "source_finding_id": finding.id,
                "source_trace_id": finding.trace.id,
                "regression_case_id": "regression-abc123",
                "status": "regression_case_created",
            }
        ],
    )

    report_finding = bundle.vulnerability_report.findings[0]
    assert report_finding.regression_case_id == "regression-abc123"
    assert report_finding.regression_status == "regression_case_created"
    assert bundle.regression_pack_summary.case_count == 1


def test_markdown_export_contains_required_operator_sections_and_no_overclaim() -> None:
    markdown = operator_artifacts_to_markdown(build_operator_artifact_bundle(make_campaign()))

    assert "## Rules of Engagement Summary" in markdown
    assert "## Vulnerability Report" in markdown
    assert "## Model/System Security Card" in markdown
    assert "## PR Checklist" in markdown
    assert "## Stakeholder Readout" in markdown
    assert "## Regression Pack Summary" in markdown
    assert "Detector hints: weak signal context only" in markdown
    assert "JudgeAgent verdict" in markdown
    assert "Detector hints: proof" not in markdown


def test_json_export_has_stable_shape() -> None:
    data = json.loads(operator_artifacts_to_json(build_operator_artifact_bundle(make_campaign())))

    assert data["schema_version"] == "redthread.operator_artifacts.v1"
    assert data["vulnerability_report"]["finding_count"] == 1
    assert data["vulnerability_report"]["findings"][0]["judge_verdict"] == "confirmed_jailbreak"
    assert data["regression_pack_summary"]["links"] == []
