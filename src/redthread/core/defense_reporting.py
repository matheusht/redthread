"""Helpers for building defense validation reports and deployment records."""

from __future__ import annotations

import hashlib

from redthread.core.defense_models import (
    DeploymentRecord,
    GuardrailProposal,
    IsolatedSegment,
    ValidationResult,
)
from redthread.core.defense_reporting_models import DefenseValidationReport


def build_validation_report(
    *,
    trace_id: str,
    proposal: GuardrailProposal,
    validation: ValidationResult,
) -> DefenseValidationReport:
    """Build the structured validation report for one defense run."""
    exploit_cases = [case.case_id for case in validation.replay_cases if case.kind == "exploit"]
    benign_cases = [case.case_id for case in validation.replay_cases if case.kind == "benign"]
    failed_cases = [case.case_id for case in validation.replay_cases if not case.passed]
    failed_case_reasons = {
        case.case_id: case.failure_reason
        for case in validation.replay_cases
        if not case.passed and case.failure_reason
    }
    exploit_passes = sum(1 for case in validation.replay_cases if case.kind == "exploit" and case.passed)
    exploit_total = sum(1 for case in validation.replay_cases if case.kind == "exploit")
    benign_passes = sum(1 for case in validation.replay_cases if case.kind == "benign" and case.passed)
    benign_total = sum(1 for case in validation.replay_cases if case.kind == "benign")
    return DefenseValidationReport(
        trace_id=trace_id,
        replay_suite_id=validation.replay_suite_id,
        validation_mode=validation.validation_mode,
        evidence_mode=validation.evidence_mode,
        evidence_label=validation.evidence_label,
        exploit_case_ids=exploit_cases,
        benign_case_ids=benign_cases,
        failed_case_ids=failed_cases,
        failed_case_reasons=failed_case_reasons,
        replay_case_count=len(validation.replay_cases),
        benign_pass_count=benign_passes,
        benign_total_count=benign_total,
        blocked_attack_summary=(
            f"exploit replays blocked {exploit_passes}/{exploit_total}"
            if validation.exploit_replay_passed
            else f"exploit replays blocked {exploit_passes}/{exploit_total} (worst score={validation.judge_score:.2f})"
        ),
        benign_utility_summary=f"benign suite {benign_passes}/{benign_total} passed",
        guardrail_clause=proposal.clause,
        rationale=proposal.rationale,
    )


def build_deployment_record(
    *,
    trace_id: str,
    proposal: GuardrailProposal,
    validation: ValidationResult,
    target_model: str,
    segment: IsolatedSegment,
) -> DeploymentRecord:
    """Build the deployment record stored in memory and promotion artifacts."""
    prompt_hash = hashlib.sha256((segment.target_system_prompt or "").encode("utf-8")).hexdigest()[:16]
    report = build_validation_report(
        trace_id=trace_id,
        proposal=proposal,
        validation=validation,
    )
    return DeploymentRecord(
        trace_id=trace_id,
        guardrail_clause=proposal.clause,
        classification=proposal.classification,
        validation=validation,
        target_model=target_model,
        target_system_prompt_hash=prompt_hash,
        validation_report=report,
        metadata={
            "rationale": proposal.rationale,
            "deployed": validation.passed,
            "replay_suite_id": validation.replay_suite_id,
            "validation_mode": validation.validation_mode,
            "evidence_mode": validation.evidence_mode,
            "failed_case_ids": report.failed_case_ids,
        },
    )


__all__ = ["build_deployment_record", "build_validation_report"]
