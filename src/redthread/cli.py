"""RedThread CLI — entry point for all commands.

Commands:
  redthread run   — execute a red-team campaign
  redthread version — print version info
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

from redthread import __version__
from redthread.config.settings import RedThreadSettings
from redthread.engine import RedThreadEngine
from redthread.models import CampaignConfig

console = Console()


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)],
    )


@click.group()
@click.version_option(__version__, "-V", "--version")
def main() -> None:
    """RedThread — Autonomous AI red-teaming engine."""
    pass


@main.command()
@click.option(
    "--objective",
    "-o",
    required=True,
    help='What to test for (e.g. "authorization bypass via identity impersonation")',
)
@click.option(
    "--system-prompt",
    "-s",
    default="You are a helpful customer service assistant.",
    show_default=True,
    help="The target agent's system prompt.",
)
@click.option(
    "--rubric",
    "-r",
    default="authorization_bypass",
    show_default=True,
    help="Judge rubric (filename without .yaml extension)",
)
@click.option(
    "--personas",
    "-n",
    default=3,
    show_default=True,
    type=int,
    help="Number of adversarial personas to generate",
)
@click.option(
    "--target-model",
    default=None,
    help="Override target model from settings",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Generate personas but skip actual attack execution",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enable debug logging",
)
@click.option(
    "--env-file",
    type=click.Path(exists=False),
    default=".env",
    help="Path to .env file",
)
def run(
    objective: str,
    system_prompt: str,
    rubric: str,
    personas: int,
    target_model: str | None,
    dry_run: bool,
    verbose: bool,
    env_file: str,
) -> None:
    """Execute a red-team campaign against a target LLM."""

    _setup_logging(verbose)

    # Load settings
    settings = RedThreadSettings(_env_file=env_file)
    if target_model:
        settings.target_model = target_model
    if dry_run:
        settings.dry_run = True

    # Print campaign header
    console.print(
        Panel.fit(
            f"[bold red]🔴 RedThread[/bold red] v{__version__}\n"
            f"[dim]Autonomous AI Red-Teaming Engine[/dim]",
            border_style="red",
        )
    )

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[dim]Objective[/dim]", f"[white]{objective}[/white]")
    table.add_row("[dim]Algorithm[/dim]", f"[cyan]{settings.algorithm.value.upper()}[/cyan]")
    table.add_row("[dim]Attacker[/dim]", f"[yellow]{settings.attacker_model}[/yellow]")
    table.add_row("[dim]Target[/dim]", f"[green]{settings.target_model}[/green]")
    table.add_row("[dim]Judge[/dim]", f"[blue]{settings.judge_model}[/blue]")
    table.add_row("[dim]Personas[/dim]", str(personas))
    table.add_row("[dim]Max iterations[/dim]", str(settings.max_iterations))
    if dry_run:
        table.add_row("[dim]Mode[/dim]", "[yellow]DRY RUN[/yellow]")
    console.print(table)
    console.print()

    config = CampaignConfig(
        objective=objective,
        target_system_prompt=system_prompt,
        rubric_name=rubric,
        num_personas=personas,
    )

    engine = RedThreadEngine(settings)

    try:
        result = asyncio.run(engine.run(config))
    except KeyboardInterrupt:
        console.print("\n[yellow]Campaign interrupted.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Campaign failed:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)

    # Print results summary
    console.print()
    asr_color = "red" if result.attack_success_rate > 0.3 else "green"
    console.print(
        Panel(
            f"[bold]Campaign Results[/bold]\n\n"
            f"  Attack Success Rate (ASR): [{asr_color}]{result.attack_success_rate:.1%}[/{asr_color}]\n"
            f"  Average G-Eval Score:      {result.average_score:.2f}/5.0\n"
            f"  Total Runs:                {len(result.results)}\n"
            f"  Transcript:                logs/{result.id}.jsonl",
            border_style=asr_color,
        )
    )

    # Print per-result table
    if result.results:
        results_table = Table(title="Per-Attack Results")
        results_table.add_column("Persona", style="cyan")
        results_table.add_column("Tactic", style="dim")
        results_table.add_column("Score", justify="center")
        results_table.add_column("Outcome", justify="center")
        results_table.add_column("Iterations", justify="center")

        for r in result.results:
            outcome_style = (
                "bold red" if r.verdict.is_jailbreak
                else "yellow" if r.trace.outcome.value == "partial"
                else "dim white" if r.trace.outcome.value == "skipped"
                else "bold yellow" if r.trace.outcome.value == "error"
                else "green"
            )
            results_table.add_row(
                r.trace.persona.name,
                r.trace.persona.tactic.name,
                f"{r.verdict.score:.1f}",
                f"[{outcome_style}]{r.trace.outcome.value.upper()}[/{outcome_style}]",
                str(r.iterations_used),
            )

        console.print(results_table)

    sys.exit(0 if result.attack_success_rate == 0.0 else 1)


@main.command()
def version() -> None:
    """Print version information."""
    console.print(f"RedThread v{__version__}")


if __name__ == "__main__":
    main()
