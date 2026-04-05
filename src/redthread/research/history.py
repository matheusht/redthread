"""Historical analysis over the autoresearch TSV ledger."""

from __future__ import annotations

import csv
from pathlib import Path

from redthread.research.models import ObjectiveScore


class ObjectiveHistoryAnalyzer:
    """Score objective slugs from prior research results."""

    def __init__(self, results_path: Path) -> None:
        self.results_path = results_path

    def rank(self) -> list[ObjectiveScore]:
        """Return objectives ranked by historical weighted score."""
        if not self.results_path.exists():
            return []

        stats: dict[str, dict[str, float]] = {}
        with self.results_path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            for row in reader:
                if row.get("mode") not in {"experiment", "supervised_lane"}:
                    continue
                slugs = [slug for slug in row.get("objective_slugs", "").split("|") if slug]
                if not slugs:
                    continue
                avg_asr = float(row.get("average_asr", 0.0) or 0.0)
                avg_score = float(row.get("average_score", 0.0) or 0.0)
                confirmed = float(row.get("confirmed_jailbreaks", 0) or 0)
                near_misses = float(row.get("near_misses", 0) or 0)
                weighted = (confirmed * 10.0) + (near_misses * 2.0) + (avg_asr * 5.0) + avg_score
                share = 1.0 / len(slugs)
                for slug in slugs:
                    item = stats.setdefault(
                        slug,
                        {
                            "attempts": 0.0,
                            "confirmed_jailbreaks": 0.0,
                            "near_misses": 0.0,
                            "average_asr": 0.0,
                            "average_score": 0.0,
                            "weighted_score": 0.0,
                        },
                    )
                    item["attempts"] += 1.0
                    item["confirmed_jailbreaks"] += confirmed * share
                    item["near_misses"] += near_misses * share
                    item["average_asr"] += avg_asr
                    item["average_score"] += avg_score
                    item["weighted_score"] += weighted * share

        ranked: list[ObjectiveScore] = []
        for slug, item in stats.items():
            attempts = max(int(item["attempts"]), 1)
            ranked.append(
                ObjectiveScore(
                    slug=slug,
                    attempts=attempts,
                    confirmed_jailbreaks=int(item["confirmed_jailbreaks"]),
                    near_misses=int(item["near_misses"]),
                    average_asr=item["average_asr"] / attempts,
                    average_score=item["average_score"] / attempts,
                    weighted_score=item["weighted_score"] / attempts,
                )
            )
        ranked.sort(key=lambda entry: entry.weighted_score, reverse=True)
        return ranked
