"""Research phase 1 and 2 CLI commands."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from redthread.cli.research.shared import research_algorithm_override_option, setup_logging
from redthread.config.settings import RedThreadSettings


def register_research_core_commands(research: click.Group, console: Console) -> None:
    @research.command(name="init")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    def research_init(env_file: str) -> None:
        """Create default autoresearch config and ledger files."""
        from redthread.research.runner import PhaseOneResearchHarness

        harness = PhaseOneResearchHarness(RedThreadSettings(_env_file=env_file), Path.cwd())
        console.print(
            Panel(
                f"[bold]Autoresearch initialized[/bold]\n\n"
                f"  Template config: {harness.workspace.template_config_path}\n"
                f"  Runtime config:  {harness.config_path}\n"
                f"  Results:         {harness.results_path}",
                border_style="cyan",
            )
        )

    @research.command(name="baseline")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    @click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug logging")
    def research_baseline(env_file: str, verbose: bool) -> None:
        """Run the frozen Phase 1 benchmark pack and write it to results.tsv."""
        from redthread.research.runner import PhaseOneResearchHarness

        setup_logging(console, verbose)
        harness = PhaseOneResearchHarness(RedThreadSettings(_env_file=env_file), Path.cwd())

        async def _run() -> None:
            summary = await harness.run_baseline()
            console.print(
                Panel(
                    f"[bold]Baseline complete[/bold]\n\n"
                    f"  Campaigns:            {summary.total_campaigns}\n"
                    f"  Confirmed jailbreaks: {summary.confirmed_jailbreaks}\n"
                    f"  Near misses:          {summary.near_misses}\n"
                    f"  Average ASR:          {summary.average_asr:.1%}\n"
                    f"  Average score:        {summary.average_score:.2f}\n"
                    f"  Composite score:      {summary.composite_score:.2f}\n"
                    f"  Results:              {harness.results_path}",
                    border_style="cyan",
                )
            )

        import asyncio
        asyncio.run(_run())

    @research.command(name="run")
    @click.option("--cycles", type=int, default=1, show_default=True, help="Number of bounded experiment cycles to run.")
    @click.option("--baseline-first", is_flag=True, default=False, help="Run the frozen baseline pack before the experiment cycles.")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    @click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug logging")
    @research_algorithm_override_option
    def research_run(cycles: int, baseline_first: bool, env_file: str, verbose: bool, algorithm: str | None) -> None:
        """Run bounded Phase 1 experiment batches and write them to results.tsv."""
        from redthread.research.runner import PhaseOneResearchHarness

        setup_logging(console, verbose)
        settings = RedThreadSettings(_env_file=env_file)
        harness = PhaseOneResearchHarness(settings, Path.cwd())
        algorithm_override = settings.algorithm.__class__(algorithm) if algorithm is not None else None

        async def _run() -> None:
            summaries = await harness.run_experiments(cycles=cycles, baseline_first=baseline_first, algorithm_override=algorithm_override)
            final = summaries[-1]
            console.print(
                Panel(
                    f"[bold]Research batch complete[/bold]\n\n"
                    f"  Algorithm override:   {algorithm_override.value if algorithm_override else 'mixed/defaults'}\n"
                    f"  Batches logged:       {len(summaries)}\n"
                    f"  Final mode:           {final.mode}\n"
                    f"  Campaigns:            {final.total_campaigns}\n"
                    f"  Confirmed jailbreaks: {final.confirmed_jailbreaks}\n"
                    f"  Near misses:          {final.near_misses}\n"
                    f"  Average ASR:          {final.average_asr:.1%}\n"
                    f"  Average score:        {final.average_score:.2f}\n"
                    f"  Composite score:      {final.composite_score:.2f}\n"
                    f"  Results:              {harness.results_path}",
                    border_style="magenta",
                )
            )

        import asyncio
        asyncio.run(_run())

    @research.command(name="supervise")
    @click.option("--cycles", type=int, default=1, show_default=True, help="Number of supervised Phase 2 cycles to run.")
    @click.option("--baseline-first", is_flag=True, default=False, help="Run the frozen baseline pack before each supervised cycle.")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    @click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug logging")
    @research_algorithm_override_option
    def research_supervise(cycles: int, baseline_first: bool, env_file: str, verbose: bool, algorithm: str | None) -> None:
        """Run Phase 2 supervisor cycles over offense, regression, and control lanes."""
        from redthread.research.supervisor import PhaseTwoResearchHarness

        setup_logging(console, verbose)
        settings = RedThreadSettings(_env_file=env_file)
        harness = PhaseTwoResearchHarness(settings, Path.cwd())
        algorithm_override = settings.algorithm.__class__(algorithm) if algorithm is not None else None

        async def _run() -> None:
            last_cycle = None
            for _ in range(cycles if cycles > 0 else 1):
                last_cycle = await harness.run_cycle(baseline_first=baseline_first, algorithm_override=algorithm_override)
            if last_cycle is not None:
                console.print(
                    Panel(
                        f"[bold]Phase 2 supervised cycle complete[/bold]\n\n"
                        f"  Algorithm override: {algorithm_override.value if algorithm_override else 'mixed/defaults'}\n"
                        f"  Accepted:      {last_cycle.accepted}\n"
                        f"  Winning lane:  {last_cycle.winning_lane}\n"
                        f"  Rationale:     {last_cycle.rationale}\n"
                        f"  Calibration:   {harness.workspace.baseline_registry_path}\n"
                        f"  Results:       {harness.results_path}",
                        border_style="blue",
                    )
                )

        import asyncio
        asyncio.run(_run())
