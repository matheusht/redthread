"""Research promotion and report inspection CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from redthread.config.settings import RedThreadSettings


def register_research_promotion_commands(research: click.Group, console: Console) -> None:
    @research.command(name="promote")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    @click.option("--dry-run", is_flag=True, default=False, help="Replay promotion validation without writing production memory.")
    def research_promote(env_file: str, dry_run: bool) -> None:
        from redthread.research.promotion import ResearchPromotionManager

        manager = ResearchPromotionManager(RedThreadSettings(_env_file=env_file), Path.cwd())
        promotion = manager.promote_latest(dry_run=dry_run)
        payload = json.loads(Path(promotion.validation_ref).read_text(encoding="utf-8"))
        lines = [
            f"  Promotion: {promotion.promotion_id}",
            f"  Proposal:  {promotion.proposal_id}",
            f"  Validation:{promotion.validation_status}",
            f"  Entries:   {promotion.promoted_deployments}",
            f"  Reports:   {len(promotion.defense_report_refs)}",
            f"  Manifest:  {promotion.manifest_ref}",
            f"  Validation:{promotion.validation_ref}",
            f"  Target:    {promotion.target_memory_dir}",
        ]
        _append_if_any(lines, "Missing reports", payload.get("missing_report_trace_ids", []))
        _append_if_any(lines, "Weak evidence", payload.get("weak_evidence_trace_ids", []))
        _append_if_any(lines, "Failed replay", payload.get("failed_validation_trace_ids", []))
        weak_records = payload.get("validation_failures_by_trace", {})
        if weak_records:
            rendered = "; ".join(f"{trace_id} -> {', '.join(failures)}" for trace_id, failures in sorted(weak_records.items()))
            lines.append(f"  Failure map: {rendered}")
        console.print(Panel("[bold]Research promotion complete[/bold]\n\n" + "\n".join(lines), border_style="green"))

    @research.command(name="promote-inspect")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    def research_promote_inspect(env_file: str) -> None:
        from redthread.research.promotion_inspection import render_latest_promotion

        try:
            rendered = render_latest_promotion(RedThreadSettings(_env_file=env_file), Path.cwd())
        except LookupError as exc:
            raise click.ClickException(str(exc)) from exc
        console.print(Panel("[bold]Latest promotion[/bold]\n\n" + rendered, border_style="cyan"))

    @research.command(name="report-inspect")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    @click.option("--memory-source", type=click.Choice(["research", "production"], case_sensitive=False), default="research", show_default=True, help="Which memory plane to inspect for deployment validation reports.")
    @click.option("--trace-id", default=None, help="Optional trace_id filter for one deployment validation report.")
    def research_report_inspect(env_file: str, memory_source: str, trace_id: str | None) -> None:
        from redthread.research.report_inspection import (
            load_validation_reports,
            render_validation_report,
        )

        try:
            records = load_validation_reports(RedThreadSettings(_env_file=env_file), Path.cwd(), memory_source.lower(), trace_id)
        except LookupError as exc:
            raise click.ClickException(str(exc)) from exc
        for record in records:
            console.print(Panel("[bold]Deployment validation report[/bold]\n\n" + render_validation_report(record, memory_source.lower()), border_style="magenta"))


def _append_if_any(lines: list[str], label: str, values: list[str]) -> None:
    if values:
        lines.append(f"  {label}: {', '.join(values)}")
