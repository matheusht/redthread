"""Helpers for summarizing promotion evidence strength and failure buckets."""

from __future__ import annotations

from dataclasses import dataclass

from redthread.core.defense_models import DeploymentRecord
from redthread.core.defense_utility_gate import evaluate_defense_record

_WEAK_EVIDENCE_PREFIXES = ("evidence_mode_not_promotable:",)
_WEAK_EVIDENCE_CHECKS = {
    "missing_validation_report",
    "missing_replay_case_evidence",
}
_FAILED_VALIDATION_CHECKS = {
    "validation_not_passed",
    "exploit_replay_not_blocked",
    "benign_suite_not_preserved",
    "replay_case_failures_present",
}


@dataclass(frozen=True)
class PromotionEvidenceSummary:
    """Structured evidence summary for one promotion attempt."""

    report_coverage: dict[str, str]
    missing_report_trace_ids: list[str]
    utility_gate: dict[str, list[str]]
    weak_evidence_trace_ids: list[str]
    failed_validation_trace_ids: list[str]
    validation_failures_by_trace: dict[str, list[str]]


def summarize_promotion_records(records: dict[str, DeploymentRecord]) -> PromotionEvidenceSummary:
    """Bucket promotion evidence failures so operators can inspect them quickly."""
    report_coverage = {
        trace_id: ("present" if record.validation_report is not None else "missing")
        for trace_id, record in sorted(records.items())
    }
    utility_gate = {
        trace_id: evaluate_defense_record(record).failed_checks
        for trace_id, record in sorted(records.items())
    }
    validation_failures_by_trace = {
        trace_id: failures for trace_id, failures in utility_gate.items() if failures
    }
    missing_report_trace_ids = [trace_id for trace_id, state in report_coverage.items() if state != "present"]
    weak_evidence_trace_ids = [
        trace_id
        for trace_id, failures in validation_failures_by_trace.items()
        if any(_is_weak_evidence_failure(failure) for failure in failures)
    ]
    failed_validation_trace_ids = [
        trace_id
        for trace_id, failures in validation_failures_by_trace.items()
        if any(failure in _FAILED_VALIDATION_CHECKS for failure in failures)
    ]
    return PromotionEvidenceSummary(
        report_coverage=report_coverage,
        missing_report_trace_ids=missing_report_trace_ids,
        utility_gate=utility_gate,
        weak_evidence_trace_ids=weak_evidence_trace_ids,
        failed_validation_trace_ids=failed_validation_trace_ids,
        validation_failures_by_trace=validation_failures_by_trace,
    )


def promotion_failure_reason(summary: PromotionEvidenceSummary) -> str | None:
    """Return the top-level failure reason for one promotion validation pass."""
    if summary.missing_report_trace_ids:
        traces = ", ".join(summary.missing_report_trace_ids)
        return f"missing promotion evidence: validation reports for {traces}"
    if summary.weak_evidence_trace_ids:
        traces = ", ".join(summary.weak_evidence_trace_ids)
        return f"weak promotion evidence: non-promotable or incomplete replay evidence for {traces}"
    if summary.failed_validation_trace_ids:
        traces = ", ".join(summary.failed_validation_trace_ids)
        return f"failed promotion validation: replay or benign utility checks failed for {traces}"
    if summary.validation_failures_by_trace:
        traces = ", ".join(sorted(summary.validation_failures_by_trace))
        return f"failed promotion validation: utility gate rejected {traces}"
    return None


def _is_weak_evidence_failure(failure: str) -> bool:
    return failure in _WEAK_EVIDENCE_CHECKS or failure.startswith(_WEAK_EVIDENCE_PREFIXES)


__all__ = [
    "PromotionEvidenceSummary",
    "promotion_failure_reason",
    "summarize_promotion_records",
]
