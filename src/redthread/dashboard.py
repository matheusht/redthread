"""Campaign Health Dashboard — Phase 5D.

Loads historical campaign JSONL transcripts and renders a Rich table
showing health trends over time:

  Campaign ID | Timestamp | Target | Mode | Runtime | Runs | ASR | ASI | Health Tier

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

import logging
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from redthread.dashboard_history import load_campaign_history

__all__ = ["load_campaign_history", "render_dashboard"]

logger = logging.getLogger(__name__)


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
    table.add_column("Mode", justify="center")
    table.add_column("Runtime", justify="center")
    table.add_column("Runs", justify="right")
    table.add_column("ASR", justify="right")
    table.add_column("ASI", justify="right")
    table.add_column("Health", justify="center")

    # Aggregates for footer
    total_runs = 0
    asr_values: list[float] = []
    asi_values: list[float] = []

    for camp in history:
        asr = camp["attack_success_rate"]
        asi = camp.get("asi_score")
        tier = camp.get("health_tier") or "—"
        is_alert = camp.get("is_alert", False)
        runs = camp.get("num_runs", 0)
        row_color = _row_color(asr, asi, is_alert)
        mode_str = _mode_cell(camp)
        runtime_str = _runtime_cell(camp, row_color)

        total_runs += runs
        asr_values.append(asr)
        if asi is not None:
            asi_values.append(asi)

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
            mode_str,
            runtime_str,
            str(runs),
            asr_str,
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
        "",
        f"[bold]{total_runs}[/bold]",
        f"[bold {footer_color}]{avg_asr:.0%}[/bold {footer_color}]",
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


def _mode_cell(campaign: dict[str, Any]) -> str:
    runtime_mode = campaign.get("runtime_mode", "unknown")
    telemetry_mode = campaign.get("telemetry_mode", "unknown")
    return f"{runtime_mode}/{telemetry_mode}"


def _runtime_cell(campaign: dict[str, Any], row_color: str) -> str:
    if not campaign.get("degraded_runtime"):
        return "[green]clean[/green]"

    attack = campaign.get("attack_worker_failures", 0)
    judge = campaign.get("judge_worker_failures", 0)
    defense = campaign.get("defense_worker_failures", 0)
    error_count = campaign.get("error_count", 0)
    return (
        f"[{row_color}]degraded {error_count}e "
        f"A{attack}/J{judge}/D{defense}[/{row_color}]"
    )
