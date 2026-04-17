"""RedThread CLI entry point."""

from __future__ import annotations

import sys

import click
from rich.console import Console

from redthread import __version__
from redthread.cli.dashboard import register_dashboard_command
from redthread.cli.doctor import run_doctor
from redthread.cli.home import render_home_screen
from redthread.cli.init_cmd import run_init
from redthread.cli.monitor import register_monitor_commands
from redthread.cli.research import register_research_commands
from redthread.cli.run import register_run_command
from redthread.cli.testing import register_test_commands
from redthread.config.settings import RedThreadSettings

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(__version__, "-V", "--version")
def main(ctx: click.Context) -> None:
    """RedThread — Autonomous AI red-teaming engine."""
    if ctx.invoked_subcommand is None:
        settings = RedThreadSettings(_env_file=".env")
        render_home_screen(console, settings, ".env")


@main.command()
def version() -> None:
    """Print version information."""
    console.print(f"RedThread v{__version__}")


@main.command()
@click.option("--env-file", type=click.Path(exists=False), default=".env")
@click.option("--force", is_flag=True, default=False, help="Overwrite env file from .env.example")
def init(env_file: str, force: bool) -> None:
    """Bootstrap local RedThread files for first use."""
    sys.exit(run_init(console, env_file, force=force))


@main.command()
@click.option("--env-file", type=click.Path(exists=False), default=".env")
def doctor(env_file: str) -> None:
    """Check local setup for the bare `redthread` command path."""
    sys.exit(run_doctor(console, RedThreadSettings(_env_file=env_file), env_file))


register_run_command(main, console)
register_monitor_commands(main, console)
register_test_commands(main, console)
register_dashboard_command(main, console)
register_research_commands(main, console)


if __name__ == "__main__":
    main()
