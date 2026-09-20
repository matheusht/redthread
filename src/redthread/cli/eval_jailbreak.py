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
from redthread.cli.eval_common import (
    emit_prompt_safe_json,
    write_report_artifact,
)
from redthread.cli.eval_jailbreak_options import (
    jailbreak_corpus_options,
    render_dry_run_console,
    run_benchmark_replay_flow,
)


def register_jailbreak_eval_command(eval_group: click.Group, console: Console) -> None:
    """Register `redthread eval jailbreak-corpus`."""

    @eval_group.command(name="jailbreak-corpus")
    @jailbreak_corpus_options
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
            run_benchmark_replay_flow(
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
    render_dry_run_console(console, report, show_hints)
