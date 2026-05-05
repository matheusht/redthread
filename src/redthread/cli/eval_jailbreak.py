"""Jailbreak corpus benchmark eval CLI command."""

from __future__ import annotations

from typing import cast

import click
from rich.console import Console

from redthread.benchmarks.dry_run import (
    BenchmarkDryRunError,
    BenchmarkSource,
    build_jailbreak_corpus_dry_run_report,
)
from redthread.benchmarks.replay import (
    BenchmarkReplayError,
    run_approved_jailbreak_replay,
    run_approved_jailbreak_replay_with_regression_handoff,
)
from redthread.cli.eval_common import (
    emit_prompt_safe_json,
    emit_report,
    write_regression_handoff_artifact,
    write_report_artifact,
)
from redthread.cli.shared import run_async_command


def register_jailbreak_eval_command(eval_group: click.Group, console: Console) -> None:
    """Register `redthread eval jailbreak-corpus`."""

    @eval_group.command(name="jailbreak-corpus")
    @click.option(
        "--source",
        type=click.Choice(["spiritual-spell", "jailbreakbench"]),
        default="spiritual-spell",
        show_default=True,
    )
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
    @click.option("--regression-out", default="", type=click.Path(exists=False), help="Write prompt-safe regression handoff JSON for approved replay.")
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
        regression_out: str,
        as_json: bool,
    ) -> None:
        """Dry-run or replay reviewed jailbreak corpus fixtures safely."""
        benchmark_source = cast(BenchmarkSource, source)
        if regression_out and not replay:
            raise click.ClickException("regression handoff requires --replay")
        if replay:
            _run_replay(
                console=console,
                benchmark_source=benchmark_source,
                fixture_id=fixture_id,
                target_id=target_id,
                allow_live_target=allow_live_target,
                objective=objective,
                system_prompt=system_prompt,
                manifest_ref=manifest_ref,
                material_root=material_root,
                report_out=report_out,
                regression_out=regression_out,
                as_json=as_json,
            )
            return
        _run_dry_run(
            console=console,
            benchmark_source=benchmark_source,
            fixture_id=fixture_id,
            family=family,
            target_id=target_id,
            allow_live_target=allow_live_target,
            limit=limit,
            show_hints=show_hints,
            report_out=report_out,
            as_json=as_json,
        )


def _run_replay(
    *,
    console: Console,
    benchmark_source: BenchmarkSource,
    fixture_id: tuple[str, ...],
    target_id: str,
    allow_live_target: bool,
    objective: str,
    system_prompt: str,
    manifest_ref: str,
    material_root: str | None,
    report_out: str,
    regression_out: str,
    as_json: bool,
) -> None:
    if len(fixture_id) != 1:
        raise click.ClickException("approved replay requires exactly one --fixture-id")
    if not manifest_ref:
        raise click.ClickException("approved replay requires --manifest-ref")
    try:
        if regression_out:
            bundle = run_async_command(
                console,
                lambda: run_approved_jailbreak_replay_with_regression_handoff(
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
            report = bundle.report
            write_regression_handoff_artifact(console, bundle.regression_handoff, regression_out, as_json)
        else:
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
    write_report_artifact(console, report, report_out, as_json)
    emit_report(console, report.model_dump(), report.summary_lines, as_json)


def _run_dry_run(
    *,
    console: Console,
    benchmark_source: BenchmarkSource,
    fixture_id: tuple[str, ...],
    family: tuple[str, ...],
    target_id: str,
    allow_live_target: bool,
    limit: int,
    show_hints: bool,
    report_out: str,
    as_json: bool,
) -> None:
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
    write_report_artifact(console, report, report_out, as_json)
    if as_json:
        emit_prompt_safe_json(report.model_dump())
        return
    console.print("[bold red]REDTHREAD JAILBREAK BENCHMARK DRY-RUN[/bold red]")
    for line in report.summary_lines:
        console.print(line)
    if show_hints:
        console.print("\n[bold]Safe planning hints[/bold]")
        for profile in report.hint_profiles:
            for line in profile.summary_lines():
                console.print(line)
