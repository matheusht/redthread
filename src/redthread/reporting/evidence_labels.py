"""Canonical operator evidence labels."""

from __future__ import annotations

from typing import Final

SEALED: Final = "sealed"
LIVE_JUDGE: Final = "live_judge"
FALLBACK: Final = "fallback"
IMPORTED_WEAK_EVIDENCE: Final = "imported_weak_evidence"
SEALED_RUNTIME_REVIEW: Final = "sealed_runtime_review"
NARROW_LIVE_INTERCEPTION_PROOF: Final = "narrow_live_interception_proof"
UNKNOWN: Final = "unknown"

CANONICAL_EVIDENCE_LABELS: Final[dict[str, str]] = {
    SEALED: "Sealed deterministic evidence",
    LIVE_JUDGE: "Live JudgeAgent evidence",
    FALLBACK: "Fallback evidence; weaker than live judge",
    IMPORTED_WEAK_EVIDENCE: "Imported weak evidence; not a finding",
    SEALED_RUNTIME_REVIEW: "Sealed runtime review evidence",
    NARROW_LIVE_INTERCEPTION_PROOF: "Narrow live interception proof",
}

_MODE_ALIASES: Final[dict[str, str]] = {
    "sealed_dry_run": SEALED,
    "sealed_heuristic": SEALED,
    "sealed_dry_run_replay": SEALED,
    "live": LIVE_JUDGE,
    "live_judge": LIVE_JUDGE,
    "live_replay": LIVE_JUDGE,
    "live_judge_fallback": FALLBACK,
    "live_validation_error": FALLBACK,
    "weak_imported_evidence": IMPORTED_WEAK_EVIDENCE,
    "sealed_runtime_review": SEALED_RUNTIME_REVIEW,
    "live_interception": NARROW_LIVE_INTERCEPTION_PROOF,
    "narrow_live_interception_proof": NARROW_LIVE_INTERCEPTION_PROOF,
}


def normalize_evidence_label(mode: str | None) -> str:
    """Map a raw mode/class string to a canonical operator label key."""
    if not mode:
        return UNKNOWN
    value = mode.lower().strip()
    if value in CANONICAL_EVIDENCE_LABELS:
        return value
    return _MODE_ALIASES.get(value, UNKNOWN)


def evidence_label_summary(modes: list[str]) -> dict[str, str]:
    """Return canonical label descriptions for observed modes."""
    labels = {normalize_evidence_label(mode) for mode in modes}
    labels.discard(UNKNOWN)
    return {label: CANONICAL_EVIDENCE_LABELS[label] for label in sorted(labels)}


__all__ = [
    "CANONICAL_EVIDENCE_LABELS",
    "FALLBACK",
    "IMPORTED_WEAK_EVIDENCE",
    "LIVE_JUDGE",
    "NARROW_LIVE_INTERCEPTION_PROOF",
    "SEALED",
    "SEALED_RUNTIME_REVIEW",
    "UNKNOWN",
    "evidence_label_summary",
    "normalize_evidence_label",
]
