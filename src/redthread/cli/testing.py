"""Test command registration."""

from __future__ import annotations

import click
from rich.console import Console

from redthread.cli.testing_golden import run_golden_evaluation


def register_test_commands(main: click.Group, console: Console) -> None:
    @main.group()
    def test() -> None:
        """Regression and evaluation test suites."""

    @test.command(name="golden")
    @click.option("--model", "-m", default=None, help="Override judge model for evaluation (e.g. gpt-4o-mini)")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    @click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug logging")
    def test_golden(model: str | None, env_file: str, verbose: bool) -> None:
        """Run regression tests across the Golden Dataset (30 traces)."""
        run_golden_evaluation(console, model, env_file, verbose)
