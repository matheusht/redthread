"""Safety guards for weak external evidence imports."""

from __future__ import annotations

FORBIDDEN_EXTERNAL_EVIDENCE_CLAIM_KEYS = frozenset({
    "benchmark_score",
    "defense_id",
    "finding_count",
    "finding_id",
    "regression_case_id",
    "scorecard",
})


def reject_external_evidence_overclaim_keys(data: object) -> None:
    """Reject imported evidence fields that imply RedThread authority."""
    if not isinstance(data, dict):
        return
    present = FORBIDDEN_EXTERNAL_EVIDENCE_CLAIM_KEYS.intersection(data)
    if present:
        joined = ", ".join(sorted(present))
        msg = f"external evidence cannot create RedThread score/finding artifacts: {joined}"
        raise ValueError(msg)
