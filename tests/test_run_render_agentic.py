"""CLI rendering tests for agentic security summaries."""

from __future__ import annotations

from io import StringIO

from rich.console import Console

from redthread.cli.run_render import render_campaign_results
from redthread.models import CampaignConfig, CampaignResult


def test_render_campaign_results_includes_agentic_security_summary() -> None:
    output = StringIO()
    result = CampaignResult(
        config=CampaignConfig(
            objective="Probe tool misuse",
            target_system_prompt="You are a guarded assistant.",
            num_personas=0,
        ),
        metadata={
            "agentic_security": {
                "action_total": 3,
                "canary_event_total": 2,
                "authorization_decision_counts": {"deny": 1},
                "amplification_metrics": {"budget_breached": True},
            }
        },
    )

    render_campaign_results(Console(file=output), result)

    rendered = output.getvalue()
    assert "Agentic Security" in rendered
    assert "Actions: 3" in rendered
    assert "Canary events: 2" in rendered
    assert "deny=1" in rendered
    assert "budget breached" in rendered.lower()
