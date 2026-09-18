"""Offline replay-bundle promotion inspection command."""

from __future__ import annotations

import json
from pathlib import Path

import click
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from redthread.evaluation.promotion_gate import evaluate_agentic_promotion
from redthread.evaluation.replay_corpus import ReplayBundle, ReplayTrace


def register_replay_commands(main: click.Group, console: Console) -> None:
    """Register offline replay commands."""

    @main.group()
    def replay() -> None:
        """Inspect agentic-security replay bundles."""

    @replay.command("run")
    @click.argument("bundle_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
    def run_replay(bundle_file: Path) -> None:
        """Evaluate one replay bundle locally without executing tools."""
        try:
            bundle = ReplayBundle.model_validate_json(bundle_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as exc:
            raise click.ClickException(f"Invalid replay bundle: {exc}") from exc

        result = evaluate_agentic_promotion(bundle)
        _render_replay_result(console, bundle, result)
        if not result["passed"]:
            raise click.exceptions.Exit(1)


def _render_replay_result(
    console: Console,
    bundle: ReplayBundle,
    result: dict[str, object],
) -> None:
    passed = bool(result["passed"])
    console.print(f"Replay bundle: {bundle.bundle_id}")
    console.print(f"Status: {'PASS' if passed else 'FAIL'}")
    console.print(f"Traces: {len(bundle.traces)} | Failures: {result['failure_count']}")
    bridge = bundle.bridge_workflow_context
    known_bridge = {
        key: bridge[key]
        for key in ("workflow_count", "applied_response_binding_count")
        if key in bridge
    }
    if known_bridge:
        console.print(f"Bridge workflow: {known_bridge}")

    failures = [str(item) for item in result["failures"]]
    table = Table(title="Replay trace results")
    for column in (
        "Trace", "Threat", "Authorization (expected/actual)",
        "Canary containment (sealed/live)", "Boundary (sealed/live)",
        "Budget (expected/actual)", "Result",
    ):
        table.add_column(column)
    for trace in bundle.traces:
        table.add_row(*_trace_row(trace, failures))
    console.print(table)
    for failure in failures:
        console.print(f"Failure: {failure}")


def _trace_row(trace: ReplayTrace, failures: list[str]) -> tuple[str, ...]:
    expected_auth = trace.expected_authorization or "-"
    actual_auth = (trace.authorization_decision or {}).get("decision", "-")
    canary = _report_pair(trace.canary_report, trace.live_canary_report, "contained")
    boundary = _report_pair(
        trace.canary_report,
        trace.live_canary_report,
        "reached_execution_boundary",
    )
    expected_budget = trace.expect_budget_stop
    actual_budget = trace.budget_decision.get("stop_triggered", "-")
    expected_budget_text = "-" if expected_budget is None else str(expected_budget)
    budget = f"expected={expected_budget_text}; actual={actual_budget}"
    trace_failed = any(failure.startswith(f"{trace.trace_id}:") for failure in failures)
    return (
        trace.trace_id,
        trace.threat,
        f"expected={expected_auth}; actual={actual_auth}",
        canary,
        boundary,
        budget,
        "FAIL" if trace_failed else "PASS",
    )


def _report_pair(sealed: dict[str, object], live: dict[str, object], key: str) -> str:
    """Render both reports because the evaluator checks both independently."""
    sealed_value = sealed.get(key, "-") if sealed else "-"
    live_value = live.get(key, "-") if live else "-"
    return f"sealed={sealed_value}; live={live_value}"
