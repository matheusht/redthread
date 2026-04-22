"""Shared helpers for research CLI commands."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from redthread.cli.shared import (
    research_algorithm_override_option,
    run_async_command,
    setup_logging,
)


def render_source_mutation_cycle(console: Console, candidate: object, proposal: object, title: str) -> None:
    console.print(
        Panel(
            f"[bold]{title}[/bold]\n\n"
            f"  Candidate:   {candidate.candidate_id}\n"
            f"  Family:      {candidate.mutation_family}\n"
            f"  Status:      {candidate.apply_status}\n"
            f"  Algorithm:   {proposal.algorithm_override or 'mixed/defaults'}\n"
            f"  Recommended: {proposal.recommended_action}\n"
            f"  Winning:     {proposal.cycle.winning_lane}\n"
            f"  Promotion:   {proposal.promotion_eligibility_status}\n"
            f"  Rationale:   {proposal.rationale}",
            border_style="cyan",
        )
    )


def render_source_mutation_inspect(console: Console, candidate: object, title: str) -> None:
    console.print(
        Panel(
            f"[bold]{title}[/bold]\n\n"
            f"  Candidate: {candidate.candidate_id}\n"
            f"  Family:    {candidate.mutation_family}\n"
            f"  Status:    {candidate.apply_status}\n"
            f"  Manifest:  {candidate.patch_manifest_path}\n"
            f"  Forward:   {candidate.forward_patch_path}\n"
            f"  Reverse:   {candidate.reverse_patch_path}",
            border_style="yellow",
        )
    )


def render_source_mutation_revert(console: Console, candidate: object, title: str) -> None:
    console.print(
        Panel(
            f"[bold]{title}[/bold]\n\n"
            f"  Candidate: {candidate.candidate_id}\n"
            f"  Status:    {candidate.apply_status}\n"
            f"  Reverse:   {candidate.reverse_patch_path}",
            border_style="magenta",
        )
    )

__all__ = [
    "research_algorithm_override_option",
    "render_source_mutation_cycle",
    "render_source_mutation_inspect",
    "render_source_mutation_revert",
    "run_async_command",
    "setup_logging",
]
