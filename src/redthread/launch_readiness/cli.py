"""CLI adapter for the named launch-readiness campaign preset."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.console import Console

from redthread.cli.run_reports import write_run_reports
from redthread.cli.shared import run_async_command
from redthread.config.settings import AlgorithmType, RedThreadSettings
from redthread.engine import RedThreadEngine
from redthread.models import CampaignConfig, CampaignResult

from .baseline import attach_live_baseline_replay
from .coordinator import run_launch_campaigns
from .evaluator import evaluate_launch_readiness
from .models import LaunchReadinessConfig
from .outputs import DEFAULT_LAUNCH_REPORT_ROOT, write_launch_readiness_reports


def execute_launch_readiness(
    console: Console,
    *,
    settings: RedThreadSettings,
    campaign_config: CampaignConfig,
    trace_all: bool,
    launch_preset: str,
    benchmark_fixture_context: dict[str, Any] | None,
    report_dir: str | None,
    report_md: str | None,
    report_json: str | None,
    report_sarif: str | None,
    include_internal_sidecars: bool,
    verbose: bool,
) -> int:
    """Run all preset strategies, persist normal reports, then print gate."""
    config = LaunchReadinessConfig(preset_name=launch_preset)
    strategy_settings: dict[str, RedThreadSettings] = {}

    async def run_strategy(strategy_id: str) -> CampaignResult:
        strategy_settings[strategy_id] = settings.model_copy(
            update={"algorithm": AlgorithmType(strategy_id)}
        )
        campaign = await RedThreadEngine(strategy_settings[strategy_id], trace_all=trace_all).run(
            campaign_config
        )
        if not strategy_settings[strategy_id].dry_run and any(
            not item.verdict.is_jailbreak for item in campaign.results
        ):
            await attach_live_baseline_replay(
                campaign,
                settings=strategy_settings[strategy_id],
                campaign_config=campaign_config,
            )
        if benchmark_fixture_context:
            campaign.metadata["benchmark_fixture_context"] = benchmark_fixture_context
        campaign.metadata["launch_strategy"] = strategy_id
        return campaign

    runs = run_async_command(
        console,
        lambda: run_launch_campaigns(run_strategy, strategies=config.required_strategies),
        error_label="Launch-readiness campaign",
        verbose=verbose,
    )
    root = Path(report_dir) if report_dir else DEFAULT_LAUNCH_REPORT_ROOT
    for strategy_id, strategy_run in runs.items():
        if strategy_run.campaign is None:
            continue
        write_run_reports(
            result=strategy_run.campaign,
            settings=strategy_settings[strategy_id],
            report_dir=str(root / "strategies" / strategy_id),
            report_md=_strategy_export_path(report_md, strategy_id),
            report_json=_strategy_export_path(report_json, strategy_id),
            report_sarif=_strategy_export_path(report_sarif, strategy_id),
            include_internal_sidecars=include_internal_sidecars,
        )
    readiness = evaluate_launch_readiness(runs, config=config)
    write_launch_readiness_reports(
        readiness,
        report_dir=report_dir,
        report_md=report_md,
        report_json=report_json,
    )
    console.print(readiness.executive_markdown, markup=False)
    return 1 if readiness.gate.decision == "blocked" else 0


def _strategy_export_path(path: str | None, strategy_id: str) -> str | None:
    if path is None:
        return None
    target = Path(path)
    return str(target.with_name(f"{target.stem}-{strategy_id}{target.suffix}"))


__all__ = ["execute_launch_readiness"]
