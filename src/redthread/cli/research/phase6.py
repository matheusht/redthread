"""Research phase 6 CLI commands."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from redthread.cli.research.shared import (
    render_source_mutation_cycle,
    render_source_mutation_inspect,
    render_source_mutation_revert,
    research_algorithm_override_option,
    setup_logging,
)
from redthread.config.settings import RedThreadSettings


def register_research_phase6_commands(research: click.Group, console: Console) -> None:
    @research.group(name="phase6")
    def research_phase6() -> None:
        """Phase 6 bounded defense prompt mutation automation."""

    @research_phase6.command(name="cycle")
    @click.option("--baseline-first", is_flag=True, default=False, help="Run the frozen baseline pack before the evaluation cycle.")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    @click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug logging")
    @research_algorithm_override_option
    def research_phase6_cycle(baseline_first: bool, env_file: str, verbose: bool, algorithm: str | None) -> None:
        from redthread.research.phase6 import PhaseSixHarness

        setup_logging(console, verbose)
        settings = RedThreadSettings(_env_file=env_file)
        harness = PhaseSixHarness(settings, Path.cwd())
        algorithm_override = settings.algorithm.__class__(algorithm) if algorithm is not None else None

        async def _run() -> None:
            candidate, proposal = await harness.run_cycle(baseline_first=baseline_first, algorithm_override=algorithm_override)
            render_source_mutation_cycle(console, candidate, proposal, "Phase 6 defense mutation cycle complete")

        import asyncio
        asyncio.run(_run())

    @research_phase6.command(name="inspect")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    def research_phase6_inspect(env_file: str) -> None:
        from redthread.research.phase6 import PhaseSixHarness

        candidate = PhaseSixHarness(RedThreadSettings(_env_file=env_file), Path.cwd()).inspect_latest()
        render_source_mutation_inspect(console, candidate, "Latest Phase 6 defense mutation")

    @research_phase6.command(name="revert")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    def research_phase6_revert(env_file: str) -> None:
        from redthread.research.phase6 import PhaseSixHarness

        candidate = PhaseSixHarness(RedThreadSettings(_env_file=env_file), Path.cwd()).revert_latest()
        render_source_mutation_revert(console, candidate, "Phase 6 defense mutation reverted")
