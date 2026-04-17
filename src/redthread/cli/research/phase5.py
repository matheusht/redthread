"""Research phase 5 and mutate alias CLI commands."""

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


def register_research_phase5_commands(research: click.Group, console: Console) -> None:
    @research.group(name="mutate")
    def research_mutate() -> None:
        """Compatibility alias for Phase 5 bounded source mutation automation."""

    @research.group(name="phase5")
    def research_phase5() -> None:
        """Phase 5 bounded source mutation automation."""

    def _settings(env_file: str) -> RedThreadSettings:
        return RedThreadSettings(_env_file=env_file)

    def _inspect(env_file: str) -> None:
        from redthread.research.phase5 import PhaseFiveHarness

        candidate = PhaseFiveHarness(_settings(env_file), Path.cwd()).inspect_latest()
        render_source_mutation_inspect(console, candidate, "Latest Phase 5 source mutation")

    def _revert(env_file: str) -> None:
        from redthread.research.phase5 import PhaseFiveHarness

        candidate = PhaseFiveHarness(_settings(env_file), Path.cwd()).revert_latest()
        render_source_mutation_revert(console, candidate, "Phase 5 source mutation reverted")

    def _cycle(baseline_first: bool, env_file: str, verbose: bool, algorithm: str | None) -> None:
        from redthread.research.phase5 import PhaseFiveHarness

        setup_logging(console, verbose)
        settings = _settings(env_file)
        harness = PhaseFiveHarness(settings, Path.cwd())
        algorithm_override = settings.algorithm.__class__(algorithm) if algorithm is not None else None

        async def _run() -> None:
            candidate, proposal = await harness.run_cycle(baseline_first=baseline_first, algorithm_override=algorithm_override)
            render_source_mutation_cycle(console, candidate, proposal, "Phase 5 source mutation cycle complete")

        import asyncio
        asyncio.run(_run())

    @research_phase5.command(name="cycle")
    @click.option("--baseline-first", is_flag=True, default=False, help="Run the frozen baseline pack before the evaluation cycle.")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    @click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug logging")
    @research_algorithm_override_option
    def research_phase5_cycle(baseline_first: bool, env_file: str, verbose: bool, algorithm: str | None) -> None:
        _cycle(baseline_first, env_file, verbose, algorithm)

    @research_mutate.command(name="cycle")
    @click.option("--baseline-first", is_flag=True, default=False, help="Run the frozen baseline pack before the evaluation cycle.")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    @click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug logging")
    @research_algorithm_override_option
    def research_mutate_cycle_alias(baseline_first: bool, env_file: str, verbose: bool, algorithm: str | None) -> None:
        _cycle(baseline_first, env_file, verbose, algorithm)

    @research_phase5.command(name="inspect")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    def research_phase5_inspect(env_file: str) -> None:
        _inspect(env_file)

    @research_mutate.command(name="inspect")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    def research_mutate_inspect_alias(env_file: str) -> None:
        _inspect(env_file)

    @research_phase5.command(name="revert")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    def research_phase5_revert(env_file: str) -> None:
        _revert(env_file)

    @research_mutate.command(name="revert")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    def research_mutate_revert_alias(env_file: str) -> None:
        _revert(env_file)
