"""Research phase 4 CLI commands."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from redthread.cli.research.shared import research_algorithm_override_option, setup_logging
from redthread.config.settings import RedThreadSettings


def register_research_phase4_commands(research: click.Group, console: Console) -> None:
    @research.group(name="phase4")
    def research_phase4() -> None:
        """Phase 4 bounded mutation automation."""

    @research_phase4.command(name="cycle")
    @click.option("--baseline-first", is_flag=True, default=False, help="Run the frozen baseline pack before the evaluation cycle.")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    @click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug logging")
    @research_algorithm_override_option
    def research_phase4_cycle(baseline_first: bool, env_file: str, verbose: bool, algorithm: str | None) -> None:
        """Apply one bounded runtime mutation and evaluate it through Phase 3."""
        from redthread.research.phase4 import PhaseFourHarness

        setup_logging(console, verbose)
        settings = RedThreadSettings(_env_file=env_file)
        harness = PhaseFourHarness(settings, Path.cwd())
        algorithm_override = settings.algorithm.__class__(algorithm) if algorithm is not None else None

        async def _run() -> None:
            candidate, proposal = await harness.run_cycle(baseline_first=baseline_first, algorithm_override=algorithm_override)
            console.print(
                Panel(
                    f"[bold]Phase 4 mutation cycle complete[/bold]\n\n"
                    f"  Mutation:     {candidate.id}\n"
                    f"  Kind:         {candidate.kind}\n"
                    f"  Description:  {candidate.description}\n"
                    f"  Algorithm:    {proposal.algorithm_override or 'mixed/defaults'}\n"
                    f"  Recommendation: {proposal.recommended_action}\n"
                    f"  Winning lane: {proposal.cycle.winning_lane}\n"
                    f"  Rationale:    {proposal.rationale}\n"
                    f"  Runtime dir:  {harness.workspace.runtime_dir}",
                    border_style="cyan",
                )
            )

        import asyncio
        asyncio.run(_run())
