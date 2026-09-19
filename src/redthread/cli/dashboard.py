"""Dashboard command registration."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from redthread.config.settings import RedThreadSettings


def register_dashboard_command(main: click.Group, console: Console) -> None:
    @main.command()
    @click.option(
        "--log-dir",
        type=click.Path(exists=False),
        default=None,
        help="Directory containing campaign JSONL transcripts (default: settings.log_dir)",
    )
    @click.option(
        "--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file"
    )
    @click.option(
        "--algorithm",
        type=str,
        default=None,
        help="Filter by algorithm (e.g. PAIR, TAP, MCTS, CRESCENDO)",
    )
    @click.option(
        "--outcome",
        type=click.Choice(["jailbreak", "benign"], case_sensitive=False),
        default=None,
        help="Filter by campaign outcome",
    )
    @click.option(
        "--since",
        type=str,
        default=None,
        help="Filter campaigns started on or after timestamp (ISO or YYYY-MM-DD)",
    )
    @click.option(
        "--export",
        "export_fmt",
        type=click.Choice(["json", "csv"], case_sensitive=False),
        default=None,
        help="Export filtered campaign history as JSON or CSV",
    )
    def dashboard(
        log_dir: str | None,
        env_file: str,
        algorithm: str | None,
        outcome: str | None,
        since: str | None,
        export_fmt: str | None,
    ) -> None:
        """Display historical campaign health metrics from JSONL transcripts."""
        from redthread.dashboard import (
            export_campaign_history,
            filter_campaign_history,
            load_campaign_history,
            render_dashboard,
        )

        settings = RedThreadSettings(_env_file=env_file)
        target_dir = Path(log_dir) if log_dir else settings.log_dir
        history = load_campaign_history(target_dir)
        filtered = filter_campaign_history(
            history,
            algorithm=algorithm,
            outcome=outcome,
            since=since,
        )

        if export_fmt:
            output = export_campaign_history(filtered, export_fmt)
            click.echo(output)
            return

        render_dashboard(filtered, console)
