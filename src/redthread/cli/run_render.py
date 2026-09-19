"""Render helpers for campaign CLI output."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from redthread import __version__
from redthread.config.settings import AlgorithmType, RedThreadSettings
from redthread.models import CampaignResult
from redthread.runtime_modes import campaign_runtime_mode


def render_campaign_header(
    console: Console,
    settings: RedThreadSettings,
    objective: str,
    personas: int,
) -> None:
    console.print(
        Panel.fit(
            f"[bold red]🔴 RedThread[/bold red] v{__version__}\n"
            f"[dim]Autonomous AI Red-Teaming Engine[/dim]",
            border_style="red",
        )
    )

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[dim]Objective[/dim]", f"[white]{objective}[/white]")
    table.add_row("[dim]Algorithm[/dim]", f"[cyan]{settings.algorithm.value.upper()}[/cyan]")
    table.add_row("[dim]Attacker[/dim]", f"[yellow]{settings.attacker_model}[/yellow]")
    table.add_row("[dim]Target[/dim]", f"[green]{settings.target_model}[/green]")
    table.add_row("[dim]Judge[/dim]", f"[blue]{settings.judge_model}[/blue]")
    table.add_row("[dim]Personas[/dim]", str(personas))
    table.add_row("[dim]Max iterations[/dim]", str(settings.max_iterations))

    if settings.algorithm == AlgorithmType.TAP:
        table.add_row("[dim]Branching factor[/dim]", str(settings.branching_factor))
        table.add_row("[dim]Tree depth[/dim]", str(settings.tree_depth))
        table.add_row("[dim]Tree width[/dim]", str(settings.tree_width))
    elif settings.algorithm == AlgorithmType.CRESCENDO:
        table.add_row("[dim]Max turns[/dim]", str(settings.crescendo_max_turns))
        table.add_row("[dim]Backtrack limit[/dim]", str(settings.crescendo_backtrack_limit))
        table.add_row("[dim]Escalation threshold[/dim]", str(settings.crescendo_escalation_threshold))
    elif settings.algorithm == AlgorithmType.MCTS:
        table.add_row("[dim]Simulations[/dim]", str(settings.mcts_simulations))
        table.add_row("[dim]Max depth[/dim]", str(settings.mcts_max_depth))
        table.add_row("[dim]Strategy branches[/dim]", str(settings.mcts_strategy_count))
        table.add_row("[dim]Exploration C[/dim]", str(settings.mcts_exploration_constant))
        table.add_row("[dim]Budget (tokens)[/dim]", f"{settings.mcts_max_budget_tokens:,}")

    mode = campaign_runtime_mode(settings)
    label = "[yellow]SEALED DRY RUN[/yellow]" if mode == "sealed_dry_run" else "[green]LIVE PROVIDER[/green]"
    table.add_row("[dim]Mode[/dim]", label)
    console.print(table)
    console.print()


def render_campaign_results(console: Console, result: CampaignResult) -> int:
    console.print()
    asr_color = "red" if result.attack_success_rate > 0.3 else "green"
    console.print(
        Panel(
            "\n".join(_campaign_result_lines(result, asr_color)),
            border_style=asr_color,
        )
    )

    if result.results:
        table = Table(title="Per-Attack Results")
        table.add_column("Persona", style="cyan")
        table.add_column("Tactic", style="dim")
        table.add_column("Score", justify="center")
        table.add_column("Outcome", justify="center")
        table.add_column("Iterations", justify="center")
        for item in result.results:
            outcome_style = (
                "bold red" if item.verdict.is_jailbreak else
                "yellow" if item.trace.outcome.value == "partial" else
                "dim white" if item.trace.outcome.value == "skipped" else
                "bold yellow" if item.trace.outcome.value == "error" else
                "green"
            )
            table.add_row(
                item.trace.persona.name,
                item.trace.persona.tactic.name,
                f"{item.verdict.score:.1f}",
                f"[{outcome_style}]{item.trace.outcome.value.upper()}[/{outcome_style}]",
                str(item.iterations_used),
            )
        console.print(table)

    return 0 if result.attack_success_rate == 0.0 else 1


def _campaign_result_lines(result: CampaignResult, asr_color: str) -> list[str]:
    metadata = result.metadata
    runtime_mode = str(metadata.get("runtime_mode", "unknown"))
    degraded = bool(metadata.get("degraded_runtime", False))
    manifest = metadata.get("operator_report_manifest")
    artifact_dir = manifest.get("artifact_dir", "") if isinstance(manifest, dict) else ""
    evidence = _format_evidence_labels(manifest)
    uncertainty = _format_evidence_uncertainty(manifest)
    status = "DEGRADED" if degraded else "clean"
    lines = [
        "[bold]Campaign Results[/bold]",
        "",
        f"  Campaign ID:               {result.id}",
        f"  Runtime Mode:              {runtime_mode}",
        f"  Runtime Status:            {status}",
        f"  Attack Success Rate (ASR): [{asr_color}]{result.attack_success_rate:.1%}[/{asr_color}]",
        f"  Average G-Eval Score:      {result.average_score:.2f}/5.0",
        f"  Total Runs:                {len(result.results)}",
    ]
    lines.append(f"  Evidence:                  {evidence or 'no labeled evidence modes'}")
    if uncertainty:
        lines.append(f"  Evidence Warning:          {uncertainty}")
    if artifact_dir:
        lines.append(f"  Report:                    {artifact_dir}")
    lines.extend(_format_agentic_security(metadata))
    lines.append(f"  Transcript:                logs/{result.id}.jsonl")
    return lines


def _format_agentic_security(metadata: dict[str, object]) -> list[str]:
    agentic = metadata.get("agentic_security")
    if not isinstance(agentic, dict):
        runtime_summary = metadata.get("runtime_summary")
        agentic = runtime_summary.get("agentic_security", {}) if isinstance(runtime_summary, dict) else {}
    if not isinstance(agentic, dict):
        return []

    actions = int(agentic.get("action_total", 0) or 0)
    canary_events = int(agentic.get("canary_event_total", 0) or 0)
    decisions = agentic.get("authorization_decision_counts", {})
    metrics = agentic.get("amplification_metrics", {})
    reports = agentic.get("canary_report") or agentic.get("live_canary_report")
    if not actions and not canary_events and not decisions and not metrics and not reports:
        return []

    lines = ["", "  Agentic Security:", f"    Actions: {actions}", f"    Canary events: {canary_events}"]
    if isinstance(decisions, dict) and decisions:
        summary = ", ".join(f"{key}={value}" for key, value in sorted(decisions.items()))
        lines.append(f"    Decisions: {summary}")
    if isinstance(metrics, dict) and metrics.get("budget_breached"):
        lines.append("    Resource budget breached")
    return lines


def _format_evidence_labels(manifest: object) -> str:
    if not isinstance(manifest, dict):
        return ""
    labels = manifest.get("evidence_labels", {})
    counts = manifest.get("evidence_mode_counts", {})
    if not isinstance(labels, dict) or not labels:
        return ""
    if not isinstance(counts, dict):
        counts = {}
    return "; ".join(
        f"{key}={counts.get(key, '?')}: {value}"
        for key, value in sorted(labels.items())
    )


def _format_evidence_uncertainty(manifest: object) -> str:
    if not isinstance(manifest, dict):
        return ""
    notes = manifest.get("evidence_uncertainty", [])
    if not isinstance(notes, list) or not notes:
        return ""
    return " | ".join(str(note) for note in notes[:2])
