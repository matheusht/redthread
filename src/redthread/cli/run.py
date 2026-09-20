"""Campaign run command registration."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console

from redthread.benchmarks.run_context import (
    BenchmarkRunContextError,
    apply_benchmark_fixture_context,
)
from redthread.cli.persona_weighting import (
    PersonaWeightingPlanFileError,
    load_persona_weighting_plan_file,
)
from redthread.cli.run_help import RunHelpCommand
from redthread.cli.run_options import apply_run_overrides, run_command_options
from redthread.cli.run_render import render_campaign_header, render_campaign_results
from redthread.cli.run_reports import write_run_reports
from redthread.cli.shared import run_async_command, setup_logging
from redthread.config.settings import RedThreadSettings
from redthread.engine import RedThreadEngine
from redthread.launch_readiness.cli import execute_launch_readiness
from redthread.models import CampaignConfig


def register_run_command(main: click.Group, console: Console) -> None:
    @main.command(cls=RunHelpCommand)
    @run_command_options
    def run(
        objective: str,
        system_prompt: str,
        rubric: str,
        personas: int,
        target_model: str | None,
        dry_run: bool,
        verbose: bool,
        env_file: str,
        algorithm: str | None,
        depth: int | None,
        width: int | None,
        branching: int | None,
        trace_all: bool,
        turns: int | None,
        simulations: int | None,
        max_budget_tokens: int | None,
        benchmark_fixture: tuple[str, ...],
        persona_weighting_plan: str | None,
        report_md: str | None,
        report_json: str | None,
        report_sarif: str | None,
        report_dir: str | None,
        preset: str | None,
        include_internal_sidecars: bool,
        cop: bool,
    ) -> None:
        """Execute a red-team campaign against a target LLM."""
        setup_logging(console, verbose)
        settings = RedThreadSettings(_env_file=env_file)
        apply_run_overrides(
            settings,
            target_model,
            algorithm,
            depth,
            width,
            branching,
            dry_run,
            turns,
            simulations,
            max_budget_tokens,
            cop,
        )
        run_objective = objective
        benchmark_context = None
        if benchmark_fixture:
            try:
                benchmark_context = apply_benchmark_fixture_context(objective, benchmark_fixture)
            except BenchmarkRunContextError as exc:
                raise click.ClickException(str(exc)) from exc
            run_objective = benchmark_context.objective
        weighting_plan_payload = {}
        if persona_weighting_plan:
            try:
                weighting_plan_payload = load_persona_weighting_plan_file(
                    Path(persona_weighting_plan)
                )
            except PersonaWeightingPlanFileError as exc:
                raise click.ClickException(str(exc)) from exc
        config = CampaignConfig(
                objective=run_objective,
                target_system_prompt=system_prompt,
                rubric_name=rubric,
                num_personas=personas,
                prompting_layer_profile=(
                    benchmark_context.prompting_layer_profile.model_dump(mode="json")
                    if benchmark_context else {}
                ),
                persona_weighting_plan=weighting_plan_payload,
        )
        if preset == "launch-readiness":
            sys.exit(execute_launch_readiness(
                console, settings=settings, campaign_config=config, trace_all=trace_all,
                launch_preset=preset, benchmark_fixture_context=(
                    benchmark_context.metadata() if benchmark_context else None
                ), report_dir=report_dir, report_md=report_md, report_json=report_json,
                report_sarif=report_sarif, include_internal_sidecars=include_internal_sidecars,
                verbose=verbose,
            ))
        render_campaign_header(console, settings, objective, personas)
        if benchmark_context:
            console.print("[bold]Benchmark Fixture Context[/bold]")
            for line in benchmark_context.summary_lines:
                console.print(line)
            console.print()
        engine = RedThreadEngine(settings, trace_all=trace_all)
        result = run_async_command(
            console,
            lambda: engine.run(config),
            error_label="Campaign",
            verbose=verbose,
        )
        if benchmark_context:
            result.metadata["benchmark_fixture_context"] = benchmark_context.metadata()
        report_write = write_run_reports(
            result=result,
            settings=settings,
            report_dir=report_dir,
            report_md=report_md,
            report_json=report_json,
            report_sarif=report_sarif,
            include_internal_sidecars=include_internal_sidecars,
        )
        if report_write.transcript_error:
            console.print(
                f"[yellow]⚠️ Transcript re-write skipped: {report_write.transcript_error}[/yellow]"
            )
        sys.exit(render_campaign_results(console, result))
