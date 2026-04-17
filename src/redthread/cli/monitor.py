"""Monitor command registration."""

from __future__ import annotations

import asyncio
import sys

import click
from rich.console import Console
from rich.panel import Panel

from redthread.cli.shared import setup_logging
from redthread.config.settings import RedThreadSettings


def register_monitor_commands(main: click.Group, console: Console) -> None:
    @main.group()
    def monitor() -> None:
        """Security Guard Daemon management."""

    @monitor.command(name="start")
    @click.option("--env-file", type=click.Path(exists=False), default=".env")
    @click.option("--verbose", "-v", is_flag=True, default=False)
    def monitor_start(env_file: str, verbose: bool) -> None:
        """Start the background monitoring daemon."""
        from redthread.daemon.monitor import SecurityGuardDaemon

        setup_logging(console, verbose)
        settings = RedThreadSettings(_env_file=env_file)
        if verbose:
            settings.verbose = True
        daemon = SecurityGuardDaemon(settings)
        try:
            asyncio.run(daemon.start())
        except KeyboardInterrupt:
            console.print("\n[yellow]Daemon interrupted. Stopping.[/yellow]")
            daemon.stop()
            sys.exit(0)

    @monitor.command(name="status")
    @click.option("--env-file", type=click.Path(exists=False), default=".env")
    def monitor_status(env_file: str) -> None:
        """Print the current ASI health score from historical DB records."""
        from redthread.telemetry.asi import AgentStabilityIndex
        from redthread.telemetry.collector import TelemetryCollector
        from redthread.telemetry.drift import DriftDetector

        settings = RedThreadSettings(_env_file=env_file)
        collector = TelemetryCollector(settings)
        drift_detector = DriftDetector(k_neighbors=5, distance_metric="cosine")
        baseline = collector.storage.load_baseline()
        if baseline:
            drift_detector.fit_baseline(baseline)
        report = AgentStabilityIndex(settings, drift_detector=drift_detector).compute(collector)
        color = "red" if report.is_alert else "green"
        warnings = report.metadata.get("evidence_warnings", [])
        warning_block = ""
        if warnings:
            rendered = "\n".join(f"    - {warning}" for warning in warnings)
            warning_block = f"\n\n  Evidence warnings:\n{rendered}"
        console.print()
        console.print(
            Panel(
                f"[bold]ASI Score:[/bold] [{color}]{report.overall_score:.1f}[/{color}] ({report.health_tier})\n\n"
                f"  Response Consistency: {report.response_consistency:.1f}/100\n"
                f"  Semantic Drift:       {report.semantic_drift:.1f}/100\n"
                f"  Operational Health:   {report.operational_health:.1f}/100\n"
                f"  Behavioral Stability: {report.behavioral_stability:.1f}/100\n"
                f"  Organic records:      {report.metadata.get('organic_records', 0)}\n"
                f"  Canary records:       {report.metadata.get('canary_records', 0)}\n"
                f"  Baseline fitted:      {report.metadata.get('baseline_fitted', False)}\n\n"
                f"  Recommendation:       {report.recommendation}{warning_block}",
                border_style=color,
                title="Daemon Status",
            )
        )
