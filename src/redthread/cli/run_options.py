"""Click options and settings overrides for `redthread run` CLI command."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

import click

from redthread.cli.run_help import show_research_help
from redthread.config.settings import AlgorithmType, RedThreadSettings

F = TypeVar("F", bound=Callable[..., Any])


def apply_run_overrides(
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
    """Apply CLI flags over base settings."""
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


def run_command_options(fn: F) -> F:
    """Decorator attaching all CLI options for `redthread run`."""
    options = [
        click.option("--objective", "-o", default="agentic security validation", show_default=True, help='What to test for (e.g. "authorization bypass via identity impersonation")'),
        click.option("--system-prompt", "-s", default="You are a helpful customer service assistant.", show_default=True, help="The target agent's system prompt."),
        click.option("--rubric", "-r", default="authorization_bypass", show_default=True, help="Judge rubric (basename). Options: authorization_bypass, authority_impersonation, urgency_and_scarcity, social_proof, fear_intimidation, reciprocity_trust, prompt_injection, insecure_output, sensitive_info."),
        click.option("--personas", "-n", default=3, show_default=True, type=int, help="Number of adversarial personas to generate"),
        click.option("--target", "--target-model", "target_model", default=None, help="Target model to test"),
        click.option("--dry-run", is_flag=True, default=False, help="Generate personas but skip actual attack execution"),
        click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug logging"),
        click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file"),
        click.option("--algorithm", "-a", type=click.Choice(["pair", "tap", "crescendo", "mcts", "agent_chain"], case_sensitive=False), default=None, help="Attack algorithm (default: pair)"),
        click.option("--depth", "-d", type=int, default=None, help="TAP maximum search depth"),
        click.option("--width", "-w", type=int, default=None, help="TAP maximum tree width"),
        click.option("--branching", "-b", type=int, default=None, help="TAP branching factor"),
        click.option("--trace-all", is_flag=True, default=False, hidden=True, help="Enable LangSmith tracing on ALL nodes including Attacker (local debugging)"),
        click.option("--turns", "-t", type=int, default=None, help="Crescendo max conversation turns"),
        click.option("--simulations", type=int, default=None, help="GS-MCTS number of simulations (overrides mcts_simulations setting)"),
        click.option("--max-budget-tokens", type=int, default=None, help="GS-MCTS token budget ceiling for early stopping (heuristic: chars // 4)"),
        click.option("--benchmark-fixture", multiple=True, hidden=True, help="Use safe metadata hints from a jailbreak benchmark fixture; may repeat."),
        click.option("--persona-weighting-plan", type=click.Path(exists=True, dir_okay=False), default=None, hidden=True, help="Use a safe adaptive persona weighting plan JSON artifact"),
        click.option("--report-md", type=click.Path(dir_okay=False), default=None, help="Write guide-style operator report as Markdown"),
        click.option("--report-json", type=click.Path(dir_okay=False), default=None, help="Write guide-style operator report as JSON"),
        click.option("--report-sarif", type=click.Path(dir_okay=False), default=None, help="Write security findings as SARIF v2.1.0 JSON"),
        click.option("--report-dir", type=click.Path(file_okay=False), default=None, help="Write standard campaign report directory"),
        click.option("--preset", type=click.Choice(["launch-readiness"], case_sensitive=False), default=None, help="Run a named campaign preset"),
        click.option("--include-internal-sidecars", is_flag=True, default=False, hidden=True, help="Expose adaptive-learning sidecars in the report manifest"),
        click.option("--cop", is_flag=True, default=False, help="Enable CoP (Composition of Principles) strategy generation — composes triggers instead of atomic strategies"),
        click.option("--show-research", is_flag=True, is_eager=True, expose_value=False, callback=show_research_help, help="Show hidden research controls and exit"),
    ]
    for option in reversed(options):
        fn = option(fn)
    return fn
