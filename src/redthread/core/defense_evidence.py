"""Defense validation evidence modes and operator labels."""

from __future__ import annotations

SEALED_DRY_RUN_REPLAY = "sealed_dry_run_replay"
LIVE_REPLAY = "live_replay"
LIVE_VALIDATION_ERROR = "live_validation_error"
UNKNOWN_VALIDATION_EVIDENCE = "unknown_validation_evidence"


def evidence_label_for(mode: str) -> str:
    """Return the operator-facing label for one defense evidence mode."""
    labels = {
        SEALED_DRY_RUN_REPLAY: "Sealed dry-run replay validation.",
        LIVE_REPLAY: "Live replay validation completed.",
        LIVE_VALIDATION_ERROR: "Live validation failed before replay evidence completed.",
        UNKNOWN_VALIDATION_EVIDENCE: "Validation evidence mode is unknown.",
    }
    return labels.get(mode, labels[UNKNOWN_VALIDATION_EVIDENCE])


def infer_evidence_mode(validation_mode: str, has_replay_cases: bool, failure_reason: str) -> str:
    """Infer a defense evidence mode when one was not set explicitly."""
    if validation_mode == "dry_run":
        return SEALED_DRY_RUN_REPLAY
    if validation_mode == "live" and has_replay_cases:
        return LIVE_REPLAY
    if validation_mode == "live" and failure_reason:
        return LIVE_VALIDATION_ERROR
    return UNKNOWN_VALIDATION_EVIDENCE


__all__ = [
    "LIVE_REPLAY",
    "LIVE_VALIDATION_ERROR",
    "SEALED_DRY_RUN_REPLAY",
    "UNKNOWN_VALIDATION_EVIDENCE",
    "evidence_label_for",
    "infer_evidence_mode",
]
