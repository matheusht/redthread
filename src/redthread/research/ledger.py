"""TSV ledger used by the Phase 1 autoresearch harness."""

from __future__ import annotations

import csv
from pathlib import Path

from redthread.research.models import ResearchBatchSummary, SupervisorCycleSummary

_HEADER = [
    "timestamp",
    "run_id",
    "mode",
    "lane",
    "objective_slugs",
    "campaign_ids",
    "total_campaigns",
    "total_results",
    "confirmed_jailbreaks",
    "near_misses",
    "average_asr",
    "average_score",
    "composite_score",
    "status",
    "description",
]


class ResearchLedger:
    """Append-only TSV ledger for baseline and experiment batches."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._ensure_header()

    def append(
        self,
        summary: ResearchBatchSummary,
        status: str,
        description: str,
    ) -> None:
        with self.path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t")
            writer.writerow([
                summary.completed_at.isoformat(),
                summary.run_id,
                summary.mode,
                summary.lane or "",
                "|".join(summary.objective_slugs),
                "|".join(summary.campaign_ids),
                summary.total_campaigns,
                summary.total_results,
                summary.confirmed_jailbreaks,
                summary.near_misses,
                f"{summary.average_asr:.6f}",
                f"{summary.average_score:.6f}",
                f"{summary.composite_score:.6f}",
                status,
                description,
            ])

    def append_decision(self, summary: SupervisorCycleSummary) -> None:
        """Append a supervisor decision row to the ledger."""
        self.append(
            ResearchBatchSummary(
                run_id=summary.run_id,
                mode="supervisor_decision",
                lane=summary.winning_lane,
                objective_slugs=[item.lane or "unknown" for item in summary.lane_summaries],
                campaign_ids=[item.run_id for item in summary.lane_summaries],
                total_campaigns=sum(item.total_campaigns for item in summary.lane_summaries),
                total_results=sum(item.total_results for item in summary.lane_summaries),
                confirmed_jailbreaks=sum(item.confirmed_jailbreaks for item in summary.lane_summaries),
                near_misses=sum(item.near_misses for item in summary.lane_summaries),
                average_asr=(
                    sum(item.average_asr for item in summary.lane_summaries) / len(summary.lane_summaries)
                    if summary.lane_summaries
                    else 0.0
                ),
                average_score=(
                    sum(item.average_score for item in summary.lane_summaries) / len(summary.lane_summaries)
                    if summary.lane_summaries
                    else 0.0
                ),
                composite_score=max(
                    (item.composite_score for item in summary.lane_summaries),
                    default=0.0,
                ),
                started_at=summary.started_at,
                completed_at=summary.completed_at,
            ),
            status="accept" if summary.accepted else "reject",
            description=summary.rationale,
        )

    def _ensure_header(self) -> None:
        header_line = "\t".join(_HEADER)
        if self.path.exists():
            existing = self.path.read_text(encoding="utf-8").splitlines()
            if existing and existing[0] == header_line:
                return
            body = existing[1:] if existing else []
            with self.path.open("w", encoding="utf-8", newline="") as handle:
                handle.write(header_line + "\n")
                if body:
                    handle.write("\n".join(body) + "\n")
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t")
            writer.writerow(_HEADER)
