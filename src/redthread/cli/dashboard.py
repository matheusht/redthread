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
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    def dashboard(log_dir: str | None, env_file: str) -> None:
        """Display historical campaign health metrics from JSONL transcripts."""
        from redthread.dashboard import load_campaign_history, render_dashboard

        settings = RedThreadSettings(_env_file=env_file)
        target_dir = Path(log_dir) if log_dir else settings.log_dir
        history = load_campaign_history(target_dir)
        render_dashboard(history, console)
