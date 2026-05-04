"""Benchmark evaluation CLI command registration."""

from __future__ import annotations

import click
from rich.console import Console

from redthread.cli.benchmark_materials import register_benchmark_material_commands
from redthread.cli.eval_jailbreak import register_jailbreak_eval_command


def register_benchmark_eval_commands(main: click.Group, console: Console) -> None:
    """Register benchmark evaluation command groups."""

    @main.group(name="eval")
    def eval_group() -> None:
        """Evaluation and benchmark commands."""

    register_benchmark_material_commands(eval_group, console)
    register_jailbreak_eval_command(eval_group, console)
