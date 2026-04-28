"""Markdown and JSON exporters for RedThread operator artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from redthread.reporting.models import FindingReport, OperatorArtifactBundle


def operator_artifacts_to_json(bundle: OperatorArtifactBundle) -> str:
    """Return stable JSON for an operator artifact bundle."""
    return json.dumps(bundle.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"


def operator_artifacts_to_markdown(bundle: OperatorArtifactBundle) -> str:
    """Return Markdown for all guide-style operator artifacts."""
    lines = [
        f"# RedThread Operator Report — {bundle.campaign_id}",
        "",
        "## Rules of Engagement Summary",
        f"- Objective: {bundle.rules_of_engagement.objective}",
        f"- Scope targets: {_join(bundle.rules_of_engagement.scope.target_ids)}",
        f"- Allowed tools: {_join(bundle.rules_of_engagement.scope.allowed_tools)}",
        f"- Denied tools: {_join(bundle.rules_of_engagement.scope.denied_tools)}",
        f"- Allowed domains: {_join(bundle.rules_of_engagement.scope.allowed_domains)}",
        f"- Risks tested: {_join(bundle.rules_of_engagement.risks_tested)}",
        f"- Strategies used: {_join(bundle.rules_of_engagement.strategies_used)}",
        "",
        "## Vulnerability Report",
        f"- Confirmed findings: {bundle.vulnerability_report.finding_count}",
        f"- Detector hint limitation: {bundle.vulnerability_report.detector_hint_limitations}",
        "",
    ]
    lines.extend(_finding_lines(bundle.vulnerability_report.findings))
    lines.extend(_verdict_lines(bundle))
    lines.extend(_security_card_lines(bundle))
    lines.extend(_checklist_lines(bundle))
    lines.extend(_stakeholder_lines(bundle))
    lines.extend(_regression_pack_lines(bundle))
    lines.extend(_persona_artifact_lines(bundle))
    lines.extend(_limitation_lines(bundle))
    return "\n".join(lines).rstrip() + "\n"


def write_operator_artifacts(
    bundle: OperatorArtifactBundle,
    *,
    markdown_path: Path | None = None,
    json_path: Path | None = None,
) -> None:
    """Write selected operator artifact exports."""
    if markdown_path is not None:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(operator_artifacts_to_markdown(bundle), encoding="utf-8")
    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(operator_artifacts_to_json(bundle), encoding="utf-8")


def _finding_lines(findings: list[FindingReport]) -> list[str]:
    if not findings:
        return ["No JudgeAgent-confirmed vulnerabilities.", ""]
    lines: list[str] = []
    for finding in findings:
        lines.extend([
            f"### Finding {finding.finding_id}",
            f"- Trace: {finding.trace_id}",
            f"- Risk: {finding.risk_plugin_id}",
            f"- Strategy: {finding.strategy_id}",
            f"- Severity: {finding.severity}",
            f"- JudgeAgent score: {finding.judge_score:.2f}",
            f"- JudgeAgent verdict: {finding.judge_verdict}",
            f"- Detector hints: weak signal context only ({finding.detector_hint_limitations})",
            f"- Detector summary: {finding.detector_hint_summary or {}}",
            f"- Defense status: {finding.defense_status}",
            f"- Regression status: {finding.regression_status}",
            f"- Regression case: {finding.regression_case_id or '(none)'}",
            "",
        ])
    return lines


def _verdict_lines(bundle: OperatorArtifactBundle) -> list[str]:
    lines = ["## JudgeAgent Verdicts"]
    for verdict in bundle.vulnerability_report.judge_verdicts:
        status = "jailbreak" if verdict.is_jailbreak else "not confirmed"
        lines.append(
            f"- {verdict.result_id} / {verdict.trace_id}: {verdict.judge_score:.2f} "
            f"({status}, rubric={verdict.rubric_name})"
        )
    return [*lines, ""]


def _security_card_lines(bundle: OperatorArtifactBundle) -> list[str]:
    card = bundle.security_card
    return [
        "## Model/System Security Card",
        f"- Target system prompt present: {card.target_system_prompt_present}",
        f"- Tested risks: {_join(card.tested_risks)}",
        f"- Tested strategies: {_join(card.tested_strategies)}",
        f"- Attack success rate: {card.attack_success_rate:.1%}",
        f"- Average JudgeAgent score: {card.average_judge_score:.2f}",
        "",
    ]


def _checklist_lines(bundle: OperatorArtifactBundle) -> list[str]:
    lines = ["## PR Checklist"]
    lines.extend(f"- [ ] {item}" for item in bundle.pr_checklist.items)
    return [*lines, ""]


def _stakeholder_lines(bundle: OperatorArtifactBundle) -> list[str]:
    readout = bundle.stakeholder_readout
    return [
        "## Stakeholder Readout",
        f"- Summary: {readout.summary}",
        f"- Evidence mode: {readout.evidence_mode}",
        f"- Total runs: {readout.total_runs}",
        f"- Confirmed findings: {readout.confirmed_findings}",
        "",
    ]


def _regression_pack_lines(bundle: OperatorArtifactBundle) -> list[str]:
    pack = bundle.regression_pack_summary
    lines = ["## Regression Pack Summary", f"- Regression links: {pack.case_count}"]
    for link in pack.links:
        lines.append(
            f"- {link.get('source_finding_id', '(unknown finding)')} → "
            f"{link.get('regression_case_id', '(unknown regression)')}"
        )
    return [*lines, ""]


def _persona_artifact_lines(bundle: OperatorArtifactBundle) -> list[str]:
    if not bundle.persona_outcome_telemetry:
        return []
    plan = bundle.adaptive_persona_weighting_plan
    return [
        "## Persona Outcome Telemetry",
        "- Evidence status: weak run metadata only; JudgeAgent owns findings.",
        f"- Total persona runs: {bundle.persona_outcome_telemetry.get('total_runs', 0)}",
        f"- Near misses: {bundle.persona_outcome_telemetry.get('near_misses', 0)}",
        f"- Confirmed JudgeAgent jailbreaks: "
        f"{bundle.persona_outcome_telemetry.get('confirmed_jailbreaks', 0)}",
        f"- Adaptive weighting plan layers: {_join(plan.get('ordered_layers', []))}",
        "- Regression evidence: only JudgeAgent-confirmed AttackResult objects qualify.",
        "",
    ]


def _limitation_lines(bundle: OperatorArtifactBundle) -> list[str]:
    lines = ["## Limitations"]
    lines.extend(f"- {limitation}" for limitation in bundle.limitations)
    return lines


def _join(items: list[str]) -> str:
    return ", ".join(items) if items else "(none)"


__all__ = [
    "operator_artifacts_to_json",
    "operator_artifacts_to_markdown",
    "write_operator_artifacts",
]
