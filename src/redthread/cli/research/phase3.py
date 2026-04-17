"""Research phase 3 CLI commands."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from redthread.cli.research.shared import research_algorithm_override_option, setup_logging
from redthread.config.settings import RedThreadSettings


def register_research_phase3_commands(research: click.Group, console: Console) -> None:
    @research.group(name="phase3")
    def research_phase3() -> None:
        """Phase 3 scheduling and git-backed evaluation."""

    @research_phase3.command(name="start")
    @click.option("--tag", required=True, help="Run tag for the dedicated autoresearch branch.")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    def research_phase3_start(tag: str, env_file: str) -> None:
        from redthread.research.phase3 import PhaseThreeHarness

        harness = PhaseThreeHarness(RedThreadSettings(_env_file=env_file), Path.cwd())
        session = harness.start_session(tag)
        console.print(
            Panel(
                f"[bold]Phase 3 session started[/bold]\n\n"
                f"  Branch:      {session.branch}\n"
                f"  Base commit: {session.base_commit}\n"
                f"  Session:     {harness.session_path}",
                border_style="green",
            )
        )

    @research_phase3.command(name="cycle")
    @click.option("--baseline-first", is_flag=True, default=False, help="Run the frozen baseline pack before the supervised cycle.")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    @click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug logging")
    @research_algorithm_override_option
    def research_phase3_cycle(baseline_first: bool, env_file: str, verbose: bool, algorithm: str | None) -> None:
        from redthread.research.phase3 import PhaseThreeHarness

        setup_logging(console, verbose)
        settings = RedThreadSettings(_env_file=env_file)
        harness = PhaseThreeHarness(settings, Path.cwd())
        algorithm_override = settings.algorithm.__class__(algorithm) if algorithm is not None else None

        async def _run() -> None:
            proposal = await harness.run_cycle(baseline_first=baseline_first, algorithm_override=algorithm_override)
            console.print(
                Panel(
                    f"[bold]Phase 3 proposal ready[/bold]\n\n"
                    f"  Proposal:    {proposal.proposal_id}\n"
                    f"  Algorithm:   {proposal.algorithm_override or 'mixed/defaults'}\n"
                    f"  Recommended: {proposal.recommended_action}\n"
                    f"  Winning:     {proposal.cycle.winning_lane}\n"
                    f"  Rationale:   {proposal.rationale}\n"
                    f"  Proposals:   {harness.proposals_dir}",
                    border_style="yellow",
                )
            )

        import asyncio
        asyncio.run(_run())

    @research_phase3.command(name="accept")
    @click.option("--message", default=None, help="Optional git commit message override.")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    def research_phase3_accept(message: str | None, env_file: str) -> None:
        from redthread.research.phase3 import PhaseThreeHarness

        commit = PhaseThreeHarness(RedThreadSettings(_env_file=env_file), Path.cwd()).accept_latest(message)
        console.print(Panel(f"[bold]Phase 3 proposal accepted in research[/bold]\n\n  Commit: {commit}", border_style="magenta"))

    @research_phase3.command(name="reject")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    def research_phase3_reject(env_file: str) -> None:
        from redthread.research.phase3 import PhaseThreeHarness

        proposal_id = PhaseThreeHarness(RedThreadSettings(_env_file=env_file), Path.cwd()).reject_latest()
        console.print(Panel(f"[bold]Phase 3 proposal rejected[/bold]\n\n  Proposal: {proposal_id}", border_style="red"))
