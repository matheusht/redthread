"""Campaign Health Dashboard — Phase 5D.

Loads historical campaign JSONL transcripts and renders a Rich table
showing health trends over time:

  Campaign ID | Timestamp | Target | Algorithm | ASR | Avg Score | ASI | Health Tier

Color coding:
  - Green:  ASR=0% and ASI≥70 (fully healthy)
  - Yellow: ASR>0% or 50≤ASI<70 (attention needed)
  - Red:    ASR>30% or ASI<50 (critical — investigate)

Usage::

    from redthread.dashboard import load_campaign_history, render_dashboard
    from rich.console import Console

    history = load_campaign_history(Path("./logs"))
    render_dashboard(history, Console())
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)


def load_campaign_history(log_dir: Path) -> list[dict[str, Any]]:
    """Scan JSONL campaign transcripts and build a chronological history list.

    Each JSONL file in log_dir matching `campaign-*.jsonl` or `*.jsonl`
    (but NOT `*_telemetry.jsonl`) is parsed:
      - Line 1: campaign summary (type=campaign_result)
      - Last line with type=asi_report: ASI health snapshot

    Returns a list of campaign records sorted by started_at (oldest first).
    """
    campaigns: list[dict[str, Any]] = []

    if not log_dir.exists():
        logger.warning("Log directory does not exist: %s", log_dir)
        return campaigns

    for jsonl_path in sorted(log_dir.glob("*.jsonl")):
        # Skip telemetry exports
        if jsonl_path.name.endswith("_telemetry.jsonl"):
            continue

        try:
            rec = _parse_campaign_jsonl(jsonl_path)
            if rec:
                campaigns.append(rec)
        except Exception as exc:
            logger.debug("Skipping %s — parse error: %s", jsonl_path.name, exc)

    # Sort chronologically
    campaigns.sort(key=lambda c: c.get("started_at", ""))
    return campaigns


def _parse_campaign_jsonl(path: Path) -> dict[str, Any] | None:
    """Parse a single campaign JSONL file into a summary dict."""
    summary: dict[str, Any] = {}
    asi_report: dict[str, Any] = {}

    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = entry.get("type", "")
            if entry_type == "campaign_result":
                summary = entry
            elif entry_type == "asi_report":
                asi_report = entry

    if not summary:
        return None

    return {
        "id": summary.get("id", path.stem)[:16],
        "started_at": summary.get("started_at", ""),
        "target_model": summary.get("target_model", "—"),
        "algorithm": summary.get("algorithm", "—").upper(),
        "attack_success_rate": summary.get("attack_success_rate", 0.0),
        "average_score": summary.get("average_score", 0.0),
        "num_runs": summary.get("num_runs", 0),
        "objective": summary.get("objective", "—"),
        # ASI from post-campaign telemetry pass (may be absent)
        "asi_score": asi_report.get("asi_score"),
        "health_tier": asi_report.get("health_tier"),
        "is_alert": asi_report.get("is_alert", False),
    }


def render_dashboard(history: list[dict[str, Any]], console: Console) -> None:
    """Render a Rich campaign health dashboard table.

    Color scheme:
      - Green row:  ASR=0 AND ASI≥70
      - Yellow row: ASR>0 OR 50≤ASI<70
      - Red row:    ASR>30% OR ASI<50 OR is_alert=True
    """
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]📊 RedThread — Campaign History Dashboard[/bold cyan]\n"
            "[dim]Historical health metrics from JSONL transcripts[/dim]",
            border_style="cyan",
        )
    )

    if not history:
        console.print("[yellow]No campaign transcripts found. Run a campaign first.[/yellow]")
        return

    table = Table(
        title=f"[bold]{len(history)} Campaign(s)[/bold]",
        show_header=True,
        header_style="bold white",
        border_style="dim",
        row_styles=["", "dim"],
    )

    table.add_column("Campaign ID", style="cyan", no_wrap=True)
    table.add_column("Timestamp", style="dim", no_wrap=True)
    table.add_column("Target", max_width=18)
    table.add_column("Algo", justify="center")
    table.add_column("Runs", justify="right")
    table.add_column("ASR", justify="right")
    table.add_column("Avg Score", justify="right")
    table.add_column("ASI", justify="right")
    table.add_column("Health", justify="center")

    # Aggregates for footer
    total_runs = 0
    asr_values: list[float] = []
    asi_values: list[float] = []

    for camp in history:
        asr = camp["attack_success_rate"]
        avg_score = camp["average_score"]
        asi = camp.get("asi_score")
        tier = camp.get("health_tier") or "—"
        is_alert = camp.get("is_alert", False)
        runs = camp.get("num_runs", 0)

        total_runs += runs
        asr_values.append(asr)
        if asi is not None:
            asi_values.append(asi)

        # Determine row style based on health
        row_color = _row_color(asr, asi, is_alert)

        # Format timestamp
        ts = camp.get("started_at", "")
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            ts_str = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            ts_str = ts[:16] if ts else "—"

        # Format values
        asr_str = f"[{row_color}]{asr:.0%}[/{row_color}]"
        asi_str = (
            f"[{row_color}]{asi:.1f}[/{row_color}]"
            if asi is not None
            else "[dim]—[/dim]"
        )
        tier_str = (
            f"[{row_color}]{tier}[/{row_color}]"
            if tier != "—"
            else "[dim]—[/dim]"
        )

        table.add_row(
            camp["id"],
            ts_str,
            camp["target_model"],
            camp["algorithm"],
            str(runs),
            asr_str,
            f"{avg_score:.2f}",
            asi_str,
            tier_str,
        )

    # Footer summary row
    avg_asr = sum(asr_values) / len(asr_values) if asr_values else 0.0
    avg_asi = sum(asi_values) / len(asi_values) if asi_values else None
    footer_color = _row_color(avg_asr, avg_asi, False)

    table.add_section()
    table.add_row(
        "[bold]AGGREGATE[/bold]",
        "",
        "",
        "",
        f"[bold]{total_runs}[/bold]",
        f"[bold {footer_color}]{avg_asr:.0%}[/bold {footer_color}]",
        "",
        f"[bold {footer_color}]{avg_asi:.1f}[/bold {footer_color}]" if avg_asi is not None else "[dim]—[/dim]",
        "",
    )

    console.print(table)
    console.print()


def _row_color(asr: float, asi: float | None, is_alert: bool) -> str:
    """Determine the display color for a row based on health signals."""
    if is_alert or asr > 0.30 or (asi is not None and asi < 50):
        return "red"
    if asr > 0.0 or (asi is not None and asi < 70):
        return "yellow"
    return "green"
