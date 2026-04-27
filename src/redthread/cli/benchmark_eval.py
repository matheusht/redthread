"""Benchmark evaluation dry-run CLI commands."""

from __future__ import annotations

import json
from typing import cast

import click
from rich.console import Console

from redthread.benchmarks.artifacts import (
    BenchmarkArtifactError,
    BenchmarkReportPayload,
    write_benchmark_report_artifact,
)
from redthread.benchmarks.dry_run import (
    BenchmarkDryRunError,
    BenchmarkSource,
    build_jailbreak_corpus_dry_run_report,
)
from redthread.benchmarks.replay import BenchmarkReplayError, run_approved_jailbreak_replay
from redthread.cli.benchmark_materials import register_benchmark_material_commands
from redthread.cli.shared import run_async_command


def register_benchmark_eval_commands(main: click.Group, console: Console) -> None:
    """Register metadata-safe benchmark evaluation commands."""

    @main.group(name="eval")
    def eval_group() -> None:
        """Evaluation and benchmark commands."""

    register_benchmark_material_commands(eval_group, console)

    @eval_group.command(name="jailbreak-corpus")
    @click.option("--source", default="spiritual-spell", show_default=True)
    @click.option("--fixture-id", multiple=True, help="Fixture id to include; may repeat.")
    @click.option("--family", multiple=True, help="Fixture family slug to include; may repeat.")
    @click.option("--target", "target_id", default="local-dev", show_default=True)
    @click.option("--allow-live-target", is_flag=True, default=False)
    @click.option("--objective", default="Approved jailbreak benchmark replay", show_default=True)
    @click.option("--system-prompt", default="You are a helpful assistant.", show_default=True)
    @click.option("--replay", is_flag=True, default=False, help="Run one approved local replay seed.")
    @click.option("--manifest-ref", default="", help="Vault manifest ref for approved replay.")
    @click.option("--material-root", default=None, type=click.Path(exists=False))
    @click.option("--limit", type=click.IntRange(min=1), default=25, show_default=True)
    @click.option("--show-hints", is_flag=True, default=False)
    @click.option("--report-out", default="", type=click.Path(exists=False), help="Write prompt-safe report JSON.")
    @click.option("--json", "as_json", is_flag=True, default=False)
    def jailbreak_corpus(
        source: str,
        fixture_id: tuple[str, ...],
        family: tuple[str, ...],
        target_id: str,
        allow_live_target: bool,
        objective: str,
        system_prompt: str,
        replay: bool,
        manifest_ref: str,
        material_root: str | None,
        limit: int,
        show_hints: bool,
        report_out: str,
        as_json: bool,
    ) -> None:
        """Dry-run a reviewed jailbreak corpus benchmark plan without raw prompts."""
        benchmark_source = cast(BenchmarkSource, source)
        if replay:
            if len(fixture_id) != 1:
                raise click.ClickException("approved replay requires exactly one --fixture-id")
            if not manifest_ref:
                raise click.ClickException("approved replay requires --manifest-ref")
            try:
                report = run_async_command(
                    console,
                    lambda: run_approved_jailbreak_replay(
                        source=benchmark_source,
                        fixture_id=fixture_id[0],
                        manifest_ref=manifest_ref,
                        objective=objective,
                        target_system_prompt=system_prompt,
                        material_root=material_root,
                        target_id=target_id,
                        allow_live_target=allow_live_target,
                    ),
                    error_label="Benchmark replay",
                )
            except BenchmarkReplayError as exc:
                raise click.ClickException(str(exc)) from exc
            _write_report_artifact(console, report, report_out, as_json)
            _emit_report(console, report.model_dump(), report.summary_lines, as_json)
            return
        try:
            report = build_jailbreak_corpus_dry_run_report(
                source=benchmark_source,
                fixture_ids=fixture_id,
                families=family,
                target_id=target_id,
                allow_live_target=allow_live_target,
                limit=limit,
                include_hints=show_hints,
            )
        except BenchmarkDryRunError as exc:
            raise click.ClickException(str(exc)) from exc
        _write_report_artifact(console, report, report_out, as_json)
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


def _write_report_artifact(
    console: Console,
    report: BenchmarkReportPayload,
    report_out: str,
    as_json: bool,
) -> None:
    if not report_out:
        return
    try:
        result = write_benchmark_report_artifact(report, report_out)
    except BenchmarkArtifactError as exc:
        raise click.ClickException(str(exc)) from exc
    if not as_json:
        console.print(f"Report written: {result.path}")


def _emit_report(
    console: Console,
    payload: dict[str, object],
    summary_lines: list[str],
    as_json: bool,
) -> None:
    if as_json:
        click.echo(json.dumps(payload, indent=2))
        return
    console.print("[bold red]REDTHREAD JAILBREAK BENCHMARK REPLAY[/bold red]")
    for line in summary_lines:
        console.print(line)
