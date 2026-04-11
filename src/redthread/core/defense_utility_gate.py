"""Utility gate for determining whether a defense record is promotable."""

from __future__ import annotations

from dataclasses import dataclass, field

from redthread.core.defense_models import DeploymentRecord

_ALLOWED_PROMOTION_MODES = {"live"}


@dataclass
class DefenseUtilityGateResult:
    """Structured promotability verdict for one defense deployment record."""

    trace_id: str
    passed: bool
    failed_checks: list[str] = field(default_factory=list)


def evaluate_defense_record(record: DeploymentRecord) -> DefenseUtilityGateResult:
    """Require strong, promotable evidence for a defense deployment record."""
    failed_checks: list[str] = []
    validation = record.validation

    if record.validation_report is None:
        failed_checks.append("missing_validation_report")
    if not validation.passed:
        failed_checks.append("validation_not_passed")
    if not validation.exploit_replay_passed:
        failed_checks.append("exploit_replay_not_blocked")
    if not validation.benign_passed:
        failed_checks.append("benign_suite_not_preserved")
    if validation.validation_mode not in _ALLOWED_PROMOTION_MODES:
        failed_checks.append(f"validation_mode_not_promotable:{validation.validation_mode}")
    if not validation.replay_cases:
        failed_checks.append("missing_replay_case_evidence")
    elif any(not case.passed for case in validation.replay_cases):
        failed_checks.append("replay_case_failures_present")

    return DefenseUtilityGateResult(
        trace_id=record.trace_id,
        passed=not failed_checks,
        failed_checks=failed_checks,
    )


__all__ = ["DefenseUtilityGateResult", "evaluate_defense_record"]
