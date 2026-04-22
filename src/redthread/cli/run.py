"""Campaign run command registration."""

from __future__ import annotations

import sys

import click
from rich.console import Console

from redthread.cli.run_render import render_campaign_header, render_campaign_results
from redthread.cli.shared import run_async_command, setup_logging
from redthread.config.settings import AlgorithmType, RedThreadSettings
from redthread.engine import RedThreadEngine
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


def register_run_command(main: click.Group, console: Console) -> None:
    @main.command()
    @click.option("--objective", "-o", required=True, help='What to test for (e.g. "authorization bypass via identity impersonation")')
    @click.option("--system-prompt", "-s", default="You are a helpful customer service assistant.", show_default=True, help="The target agent's system prompt.")
    @click.option("--rubric", "-r", default="authorization_bypass", show_default=True, help="Judge rubric (basename). Options: authorization_bypass, authority_impersonation, urgency_and_scarcity, social_proof, fear_intimidation, reciprocity_trust, prompt_injection, insecure_output, sensitive_info.")
    @click.option("--personas", "-n", default=3, show_default=True, type=int, help="Number of adversarial personas to generate")
    @click.option("--target-model", default=None, help="Override target model from settings")
    @click.option("--dry-run", is_flag=True, default=False, help="Generate personas but skip actual attack execution")
    @click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug logging")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    @click.option("--algorithm", "-a", type=click.Choice(["pair", "tap", "crescendo", "mcts"], case_sensitive=False), default=None, help="Attack algorithm (default: pair)")
    @click.option("--depth", "-d", type=int, default=None, help="TAP maximum search depth")
    @click.option("--width", "-w", type=int, default=None, help="TAP maximum tree width")
    @click.option("--branching", "-b", type=int, default=None, help="TAP branching factor")
    @click.option("--trace-all", is_flag=True, default=False, help="Enable LangSmith tracing on ALL nodes including Attacker (local debugging)")
    @click.option("--turns", "-t", type=int, default=None, help="Crescendo max conversation turns")
    @click.option("--simulations", type=int, default=None, help="GS-MCTS number of simulations (overrides mcts_simulations setting)")
    @click.option("--max-budget-tokens", type=int, default=None, help="GS-MCTS token budget ceiling for early stopping (heuristic: chars // 4)")
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
        )
        render_campaign_header(console, settings, objective, personas)
        config = CampaignConfig(
            objective=objective,
            target_system_prompt=system_prompt,
            rubric_name=rubric,
            num_personas=personas,
        )
        engine = RedThreadEngine(settings, trace_all=trace_all)
        result = run_async_command(
            console,
            lambda: engine.run(config),
            error_label="Campaign",
            verbose=verbose,
        )
        sys.exit(render_campaign_results(console, result))
