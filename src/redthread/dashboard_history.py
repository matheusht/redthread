"""Campaign history loading, filtering, and export helpers for the dashboard."""

from __future__ import annotations

import csv
import io
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_campaign_history(log_dir: Path) -> list[dict[str, Any]]:
    """Scan JSONL transcripts and build a chronological campaign history list."""
    campaigns: list[dict[str, Any]] = []

    if not log_dir.exists():
        logger.warning("Log directory does not exist: %s", log_dir)
        return campaigns

    for jsonl_path in sorted(log_dir.glob("*.jsonl")):
        if jsonl_path.name.endswith("_telemetry.jsonl"):
            continue

        try:
            record = parse_campaign_jsonl(jsonl_path)
            if record:
                campaigns.append(record)
        except Exception as exc:  # pragma: no cover - defensive parse guard
            logger.debug("Skipping %s — parse error: %s", jsonl_path.name, exc)

    campaigns.sort(key=lambda campaign: campaign.get("started_at", ""))
    return campaigns


def parse_campaign_jsonl(path: Path) -> dict[str, Any] | None:
    """Parse one campaign JSONL file into a dashboard record."""
    summary: dict[str, Any] = {}
    asi_report: dict[str, Any] = {}

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            if entry.get("type") == "campaign_result":
                summary = entry
            elif entry.get("type") == "asi_report":
                asi_report = entry

    if not summary:
        return None

    runtime_summary = summary.get("runtime_summary", {})
    return {
        "id": summary.get("id", path.stem)[:16],
        "started_at": summary.get("started_at", ""),
        "target_model": summary.get("target_model", "—"),
        "algorithm": summary.get("algorithm", "—").upper(),
        "runtime_mode": summary.get("runtime_mode", "unknown"),
        "telemetry_mode": summary.get("telemetry_mode", "unknown"),
        "degraded_runtime": summary.get("degraded_runtime", False),
        "error_count": summary.get("error_count", 0),
        "attack_worker_failures": runtime_summary.get("attack_worker_failures", 0),
        "judge_worker_failures": runtime_summary.get("judge_worker_failures", 0),
        "defense_worker_failures": runtime_summary.get("defense_worker_failures", 0),
        "attack_success_rate": summary.get("attack_success_rate", 0.0),
        "average_score": summary.get("average_score", 0.0),
        "num_runs": summary.get("num_runs", 0),
        "objective": summary.get("objective", "—"),
        "asi_score": asi_report.get("asi_score"),
        "health_tier": asi_report.get("health_tier"),
        "is_alert": asi_report.get("is_alert", False),
    }


def filter_campaign_history(
    campaigns: list[dict[str, Any]],
    *,
    algorithm: str | None = None,
    outcome: str | None = None,
    since: str | None = None,
) -> list[dict[str, Any]]:
    """Filter loaded campaigns by algorithm, outcome (jailbreak/benign), and timestamp."""
    filtered = list(campaigns)

    if algorithm:
        algo_upper = algorithm.strip().upper()
        filtered = [c for c in filtered if c.get("algorithm", "").upper() == algo_upper]

    if outcome:
        out_lower = outcome.strip().lower()
        if out_lower == "jailbreak":
            filtered = [
                c for c in filtered if c.get("attack_success_rate", 0.0) > 0 or c.get("is_alert")
            ]
        elif out_lower == "benign":
            filtered = [
                c
                for c in filtered
                if c.get("attack_success_rate", 0.0) == 0.0 and not c.get("is_alert")
            ]

    if since:
        since_str = since.strip()
        filtered = [c for c in filtered if c.get("started_at", "") >= since_str]

    return filtered


def export_campaign_history(campaigns: list[dict[str, Any]], fmt: str) -> str:
    """Serialize campaigns list into JSON or CSV string."""
    fmt_lower = fmt.strip().lower()
    if fmt_lower == "json":
        return json.dumps(campaigns, indent=2)
    if fmt_lower == "csv":
        output = io.StringIO()
        fieldnames = [
            "id",
            "started_at",
            "target_model",
            "algorithm",
            "runtime_mode",
            "telemetry_mode",
            "num_runs",
            "attack_success_rate",
            "average_score",
            "asi_score",
            "health_tier",
            "is_alert",
            "degraded_runtime",
            "error_count",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for camp in campaigns:
            writer.writerow(camp)
        return output.getvalue()
    raise ValueError(f"Unsupported export format: {fmt}. Use 'json' or 'csv'.")
