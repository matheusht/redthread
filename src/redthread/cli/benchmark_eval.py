"""Benchmark evaluation dry-run CLI commands."""

from __future__ import annotations

import json
from typing import cast

import click
from rich.console import Console

from redthread.benchmarks.dry_run import (
    BenchmarkDryRunError,
    BenchmarkSource,
    build_jailbreak_corpus_dry_run_report,
)


def register_benchmark_eval_commands(main: click.Group, console: Console) -> None:
    """Register metadata-safe benchmark evaluation commands."""

    @main.group(name="eval")
    def eval_group() -> None:
        """Evaluation and benchmark commands."""

    @eval_group.command(name="jailbreak-corpus")
    @click.option("--source", default="spiritual-spell", show_default=True)
    @click.option("--fixture-id", multiple=True, help="Fixture id to include; may repeat.")
    @click.option("--family", multiple=True, help="Fixture family slug to include; may repeat.")
    @click.option("--target", "target_id", default="local-dev", show_default=True)
    @click.option("--allow-live-target", is_flag=True, default=False)
    @click.option("--limit", type=click.IntRange(min=1), default=25, show_default=True)
    @click.option("--show-hints", is_flag=True, default=False)
    @click.option("--json", "as_json", is_flag=True, default=False)
    def jailbreak_corpus(
        source: str,
        fixture_id: tuple[str, ...],
        family: tuple[str, ...],
        target_id: str,
        allow_live_target: bool,
        limit: int,
        show_hints: bool,
        as_json: bool,
    ) -> None:
        """Dry-run a reviewed jailbreak corpus benchmark plan without raw prompts."""
        try:
            report = build_jailbreak_corpus_dry_run_report(
                source=cast(BenchmarkSource, source),
                fixture_ids=fixture_id,
                families=family,
                target_id=target_id,
                allow_live_target=allow_live_target,
                limit=limit,
                include_hints=show_hints,
            )
        except BenchmarkDryRunError as exc:
            raise click.ClickException(str(exc)) from exc
        if as_json:
            click.echo(json.dumps(report.model_dump(), indent=2))
            return
        console.print("[bold red]REDTHREAD JAILBREAK BENCHMARK DRY-RUN[/bold red]")
        for line in report.summary_lines:
            console.print(line)
        if show_hints:
            console.print("\n[bold]Safe planning hints[/bold]")
            for profile in report.hint_profiles:
                for line in profile.summary_lines():
                    console.print(line)
