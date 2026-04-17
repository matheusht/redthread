"""CLI home screen renderer for bare `redthread` invocations."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from redthread import __version__
from redthread.config.settings import RedThreadSettings
from redthread.runtime_modes import campaign_runtime_mode


def render_home_screen(console: Console, settings: RedThreadSettings, env_file: str) -> None:
    console.print(
        Panel.fit(
            f"[bold red]REDTHREAD[/bold red] v{__version__}\n"
            "[dim]Autonomous AI red-teaming engine[/dim]",
            border_style="red",
        )
    )

    summary = Table(show_header=False, box=None, padding=(0, 2))
    summary.add_row("[dim]Env file[/dim]", env_file)
    summary.add_row("[dim]Mode[/dim]", _mode_label(settings))
    summary.add_row("[dim]Algorithm[/dim]", settings.algorithm.value.upper())
    summary.add_row("[dim]Target[/dim]", settings.target_model)
    summary.add_row("[dim]Attacker[/dim]", settings.attacker_model)
    summary.add_row("[dim]Judge[/dim]", settings.judge_model)
    summary.add_row("[dim]Logs[/dim]", str(settings.log_dir))
    console.print(summary)
    console.print()

    commands = Table(title="Quick commands")
    commands.add_column("Command", style="cyan")
    commands.add_column("What it does")
    commands.add_row("redthread init", "create local .env and workspace dirs")
    commands.add_row("redthread run ...", "run one campaign")
    commands.add_row("redthread doctor", "check local setup")
    commands.add_row("redthread dashboard", "show campaign history")
    commands.add_row("redthread monitor status", "show ASI health status")
    commands.add_row("redthread test golden", "run golden regression")
    console.print(commands)

    install_hint = Table(show_header=False, box=None, padding=(0, 1))
    install_hint.add_row("[dim]Tip[/dim]", "Install global command with `uv tool install -e .`")
    if not Path(env_file).exists() and Path(".env.example").exists():
        install_hint.add_row("[dim]Setup[/dim]", f"Copy `.env.example` to `{env_file}`")
    install_hint.add_row("[dim]Help[/dim]", "Use `redthread --help` for full command list")
    console.print()
    console.print(Panel(install_hint, border_style="cyan", title="Get started"))


def _mode_label(settings: RedThreadSettings) -> str:
    mode = campaign_runtime_mode(settings)
    return "SEALED DRY RUN" if mode == "sealed_dry_run" else "LIVE PROVIDER"
