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
from redthread.cli.run_help import RunHelpCommand, show_research_help
from redthread.cli.run_render import render_campaign_header, render_campaign_results
from redthread.cli.run_reports import write_run_reports
from redthread.cli.shared import run_async_command, setup_logging
from redthread.config.settings import AlgorithmType, RedThreadSettings
from redthread.engine import RedThreadEngine
from redthread.launch_readiness.cli import execute_launch_readiness
from redthread.models import CampaignConfig


def _apply_run_overrides(
    settings: RedThreadSettings,
    target_model: str | None,
    algorithm: str | None,
    depth: int | None,
    width: int | None,
    branching: int | None,
    dry_run: bool,
    turns: int | None,
    simulations: int | None,
    max_budget_tokens: int | None,
    use_cop: bool,
) -> None:
    if target_model:
        settings.target_model = target_model
    if algorithm:
        settings.algorithm = AlgorithmType(algorithm)
    if depth is not None:
        settings.tree_depth = depth
    if width is not None:
        settings.tree_width = width
    if branching is not None:
        settings.branching_factor = branching
    if dry_run:
        settings.dry_run = True
    if turns is not None:
        settings.crescendo_max_turns = turns
    if simulations is not None:
        settings.mcts_simulations = simulations
    if max_budget_tokens is not None:
        settings.mcts_max_budget_tokens = max_budget_tokens
    if use_cop:
        settings.use_cop = True


def register_run_command(main: click.Group, console: Console) -> None:
    @main.command(cls=RunHelpCommand)
    @click.option("--objective", "-o", default="agentic security validation", show_default=True, help='What to test for (e.g. "authorization bypass via identity impersonation")')
    @click.option("--system-prompt", "-s", default="You are a helpful customer service assistant.", show_default=True, help="The target agent's system prompt.")
    @click.option("--rubric", "-r", default="authorization_bypass", show_default=True, help="Judge rubric (basename). Options: authorization_bypass, authority_impersonation, urgency_and_scarcity, social_proof, fear_intimidation, reciprocity_trust, prompt_injection, insecure_output, sensitive_info.")
    @click.option("--personas", "-n", default=3, show_default=True, type=int, help="Number of adversarial personas to generate")
    @click.option("--target", "--target-model", "target_model", default=None, help="Target model to test")
    @click.option("--dry-run", is_flag=True, default=False, help="Generate personas but skip actual attack execution")
    @click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug logging")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    @click.option("--algorithm", "-a", type=click.Choice(["pair", "tap", "crescendo", "mcts", "agent_chain"], case_sensitive=False), default=None, help="Attack algorithm (default: pair)")
    @click.option("--depth", "-d", type=int, default=None, help="TAP maximum search depth")
    @click.option("--width", "-w", type=int, default=None, help="TAP maximum tree width")
    @click.option("--branching", "-b", type=int, default=None, help="TAP branching factor")
    @click.option("--trace-all", is_flag=True, default=False, hidden=True, help="Enable LangSmith tracing on ALL nodes including Attacker (local debugging)")
    @click.option("--turns", "-t", type=int, default=None, help="Crescendo max conversation turns")
    @click.option("--simulations", type=int, default=None, help="GS-MCTS number of simulations (overrides mcts_simulations setting)")
    @click.option("--max-budget-tokens", type=int, default=None, help="GS-MCTS token budget ceiling for early stopping (heuristic: chars // 4)")
    @click.option("--benchmark-fixture", multiple=True, hidden=True, help="Use safe metadata hints from a jailbreak benchmark fixture; may repeat.")
    @click.option("--persona-weighting-plan", type=click.Path(exists=True, dir_okay=False), default=None, hidden=True, help="Use a safe adaptive persona weighting plan JSON artifact")
    @click.option("--report-md", type=click.Path(dir_okay=False), default=None, help="Write guide-style operator report as Markdown")
    @click.option("--report-json", type=click.Path(dir_okay=False), default=None, help="Write guide-style operator report as JSON")
    @click.option("--report-sarif", type=click.Path(dir_okay=False), default=None, help="Write security findings as SARIF v2.1.0 JSON")
    @click.option("--report-dir", type=click.Path(file_okay=False), default=None, help="Write standard campaign report directory")
    @click.option("--preset", type=click.Choice(["launch-readiness"], case_sensitive=False), default=None, help="Run a named campaign preset")
    @click.option("--include-internal-sidecars", is_flag=True, default=False, hidden=True, help="Expose adaptive-learning sidecars in the report manifest")
    @click.option("--cop", is_flag=True, default=False, help="Enable CoP (Composition of Principles) strategy generation — composes triggers instead of atomic strategies")
    @click.option("--show-research", is_flag=True, is_eager=True, expose_value=False, callback=show_research_help, help="Show hidden research controls and exit")
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
        _apply_run_overrides(
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
