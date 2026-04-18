from __future__ import annotations

from dataclasses import asdict
from typing import Any

from redthread.pyrit_adapters.execution_records import ExecutionRecord

ExecutionTruthSummary = dict[str, Any]


def build_execution_truth_summary(
    records: list[ExecutionRecord],
    *,
    sample_size: int = 5,
) -> ExecutionTruthSummary:
    seam_counts: dict[str, int] = {}
    evidence_counts: dict[str, int] = {}
    failed_count = 0
    for record in records:
        seam_counts[record.seam] = seam_counts.get(record.seam, 0) + 1
        evidence_counts[record.evidence_class] = evidence_counts.get(record.evidence_class, 0) + 1
        failed_count += 0 if record.success else 1
    return {
        "execution_record_total": len(records),
        "failed_execution_count": failed_count,
        "successful_execution_count": len(records) - failed_count,
        "seam_counts": seam_counts,
        "evidence_class_counts": evidence_counts,
        "live_seams_seen": sorted(seam_counts),
        "record_sample": [serialize_execution_record(record) for record in records[:sample_size]],
    }


def serialize_execution_record(record: ExecutionRecord) -> dict[str, Any]:
    return asdict(record)
