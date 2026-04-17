"""Research daemon and checkpoint CLI commands."""

from __future__ import annotations

import asyncio
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from redthread.cli.research.shared import setup_logging
from redthread.config.settings import RedThreadSettings


def register_research_daemon_commands(research: click.Group, console: Console) -> None:
    @research.group(name="daemon")
    def research_daemon() -> None:
        """Resume-safe daemon commands for bounded research execution."""

    @research_daemon.command(name="start")
    @click.option("--create-session", default=None, help="Optionally create a Phase 3 session before starting.")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    @click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug logging")
    def research_daemon_start(create_session: str | None, env_file: str, verbose: bool) -> None:
        from redthread.research.daemon import ResearchDaemon

        setup_logging(console, verbose)
        state = asyncio.run(ResearchDaemon(RedThreadSettings(_env_file=env_file), Path.cwd()).start(create_session_tag=create_session))
        note = "\n  Note:      Awaiting manual Phase 3 review" if state.status == "awaiting_review" else ""
        console.print(Panel(f"[bold]Research daemon stopped[/bold]\n\n  Session:   {state.session_tag}\n  Branch:    {state.branch}\n  Status:    {state.status}\n  Step:      {state.last_completed_step}\n  Proposal:  {state.latest_proposal_id}\n  Candidate: {state.latest_candidate_id}\n  Failures:  {state.consecutive_failures}{note}", border_style="cyan"))

    @research_daemon.command(name="status")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    def research_daemon_status(env_file: str) -> None:
        from redthread.research.daemon import ResearchDaemon

        status = ResearchDaemon(RedThreadSettings(_env_file=env_file), Path.cwd()).status()
        note = "\n  Note:       Awaiting manual Phase 3 review" if status.status == "awaiting_review" else ""
        console.print(Panel(f"[bold]Research daemon status[/bold]\n\n  Session:    {status.session_tag}\n  Branch:     {status.branch}\n  Active:     {status.active_lock}\n  Stale:      {status.stale_lock}\n  Heartbeat:  {status.last_heartbeat_at}\n  Step:       {status.current_step}\n  Status:     {status.status}\n  Proposal:   {status.latest_proposal_id}\n  Candidate:  {status.latest_candidate_id}\n  Failures:   {status.consecutive_failures}\n  Cooldown:   {status.cooldown_until}{note}", border_style="yellow"))

    @research_daemon.command(name="stop")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    def research_daemon_stop(env_file: str) -> None:
        from redthread.research.daemon import ResearchDaemon

        state = ResearchDaemon(RedThreadSettings(_env_file=env_file), Path.cwd()).stop()
        console.print(Panel(f"[bold]Research daemon stop requested[/bold]\n\n  Session: {state.session_tag}\n  Status:  {state.status}", border_style="magenta"))

    @research.command(name="resume")
    @click.option("--create-session", default=None, help="Optionally create a Phase 3 session before resuming.")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    @click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug logging")
    def research_resume(create_session: str | None, env_file: str, verbose: bool) -> None:
        from redthread.research.daemon import ResearchDaemon

        setup_logging(console, verbose)
        state = asyncio.run(ResearchDaemon(RedThreadSettings(_env_file=env_file), Path.cwd()).resume(create_session_tag=create_session))
        note = "\n  Note:    Awaiting manual Phase 3 review" if state.status == "awaiting_review" else ""
        console.print(Panel(f"[bold]Research resume complete[/bold]\n\n  Session:  {state.session_tag}\n  Status:   {state.status}\n  Step:     {state.last_completed_step}\n  Proposal: {state.latest_proposal_id}{note}", border_style="green"))

    @research.group(name="checkpoints")
    def research_checkpoints() -> None:
        """Inspect resumable research and promotion checkpoints."""

    @research_checkpoints.command(name="list")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    def research_checkpoints_list(env_file: str) -> None:
        from redthread.research.checkpoints import list_checkpoint_paths
        from redthread.research.workspace import ResearchWorkspace

        workspace = ResearchWorkspace(Path.cwd())
        workspace.ensure_layout()
        rows = list_checkpoint_paths(workspace.runtime_dir)
        body = "\n".join(f"  {path}" for path in rows) if rows else "  none"
        console.print(Panel(f"[bold]Research checkpoints[/bold]\n\n{body}", border_style="blue"))

    @research_checkpoints.command(name="inspect")
    @click.option("--path", "checkpoint_path", required=True, help="Checkpoint artifact path to inspect.")
    def research_checkpoints_inspect(checkpoint_path: str) -> None:
        from redthread.research.checkpoints import inspect_checkpoint

        payload = inspect_checkpoint(Path(checkpoint_path))
        console.print(Panel(f"[bold]Checkpoint[/bold]\n\n{payload}", border_style="green"))

    @research.command(name="clean-runtime")
    @click.option("--env-file", type=click.Path(exists=False), default=".env", help="Path to .env file")
    def research_clean_runtime(env_file: str) -> None:
        from redthread.research.runner import PhaseOneResearchHarness

        harness = PhaseOneResearchHarness(RedThreadSettings(_env_file=env_file), Path.cwd())
        harness.workspace.clean_runtime()
        console.print(Panel(f"[bold]Autoresearch runtime cleaned[/bold]\n\n  Runtime dir: {harness.workspace.runtime_dir}", border_style="red"))
