from __future__ import annotations

from redthread.reporting.evidence_labels import evidence_label_summary, normalize_evidence_label


def test_normalize_evidence_label_maps_required_operator_classes() -> None:
    assert normalize_evidence_label("sealed_dry_run") == "sealed"
    assert normalize_evidence_label("live_judge") == "live_judge"
    assert normalize_evidence_label("live_judge_fallback") == "fallback"
    assert normalize_evidence_label("weak_imported_evidence") == "imported_weak_evidence"
    assert normalize_evidence_label("sealed_runtime_review") == "sealed_runtime_review"
    assert normalize_evidence_label("live_interception") == "narrow_live_interception_proof"


def test_evidence_label_summary_deduplicates_observed_modes() -> None:
    summary = evidence_label_summary(["sealed_dry_run", "sealed_heuristic", "live_judge"])

    assert sorted(summary) == ["live_judge", "sealed"]
