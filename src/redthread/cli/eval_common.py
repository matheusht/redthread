"""Shared helpers for benchmark eval CLI commands."""

from __future__ import annotations

import json

import click
from rich.console import Console

from redthread.benchmarks.artifacts import (
    BenchmarkArtifactError,
    BenchmarkReportPayload,
    assert_prompt_safe_benchmark_payload,
    write_benchmark_report_artifact,
)
from redthread.benchmarks.regression_handoff import (
    BenchmarkRegressionHandoffArtifact,
    BenchmarkRegressionHandoffError,
    write_benchmark_regression_handoff_artifact,
)


def write_report_artifact(
    console: Console,
    report: BenchmarkReportPayload,
    report_out: str,
    as_json: bool,
) -> None:
    """Write a prompt-safe benchmark report when requested."""
    if not report_out:
        return
    try:
        result = write_benchmark_report_artifact(report, report_out)
    except BenchmarkArtifactError as exc:
        raise click.ClickException(str(exc)) from exc
    if not as_json:
        console.print(f"Report written: {result.path}")


def write_regression_handoff_artifact(
    console: Console,
    handoff: BenchmarkRegressionHandoffArtifact | None,
    regression_out: str,
    as_json: bool,
) -> None:
    """Write a prompt-safe benchmark regression handoff when requested."""
    if handoff is None:
        raise click.ClickException("benchmark replay did not produce a regression handoff")
    try:
        path = write_benchmark_regression_handoff_artifact(handoff, regression_out)
    except BenchmarkRegressionHandoffError as exc:
        raise click.ClickException(str(exc)) from exc
    if not as_json:
        console.print(f"Regression handoff written: {path}")


def emit_prompt_safe_json(payload: dict[str, object]) -> None:
    """Emit benchmark JSON only after prompt-safe validation."""
    try:
        assert_prompt_safe_benchmark_payload(payload)
    except BenchmarkArtifactError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(payload, indent=2))


def emit_report(
    console: Console,
    payload: dict[str, object],
    summary_lines: list[str],
    as_json: bool,
) -> None:
    """Emit a benchmark replay report to stdout."""
    if as_json:
        emit_prompt_safe_json(payload)
        return
    console.print("[bold red]REDTHREAD JAILBREAK BENCHMARK REPLAY[/bold red]")
    for line in summary_lines:
        console.print(line)
