"""Prompt-safe launch-readiness packet and executive Markdown rendering."""

from __future__ import annotations

from typing import Any

from .models import (
    LaunchGateSummary,
    LaunchReadinessConfig,
    LaunchReadinessResult,
    StrategyReadiness,
)


def build_sanitized_packet(
    config: LaunchReadinessConfig,
    strategies: list[StrategyReadiness],
    gate: LaunchGateSummary,
) -> dict[str, Any]:
    """Build a bounded packet with counts and statuses, never prompts or responses."""
    packet: dict[str, Any] = {
        "schema_version": "redthread.launch_readiness_packet.v1",
        "preset_name": config.preset_name,
        "decision": gate.decision,
        "promotable": gate.promotable,
        "gates": dict(gate.gates),
        "reasons": list(gate.reasons),
        "unknowns": list(gate.unknowns),
        "reproduction_details": "[omitted: prompt-safe packet excludes prompts and responses]",
        "strategies": [
            {
                "strategy_id": item.strategy_id,
                "status": item.status,
                "run_count": item.run_count,
                "finding_count": item.finding_count,
                "high_finding_count": item.high_finding_count,
                "evidence_labels": list(item.evidence_labels),
                "live_judge": item.live_judge,
                "fallback_evidence": item.fallback_evidence,
                "replay_passed": item.replay_passed,
                "benign_replay_passed": item.benign_replay_passed,
            }
            for item in strategies
        ],
    }
    return packet


def render_executive_markdown(result: LaunchReadinessResult) -> str:
    """Render decision and gates before findings for executive review."""
    gate = result.gate
    lines = [
        f"# Launch Readiness — {result.config.preset_name}",
        "",
        "## Executive Decision",
        f"- Decision: **{gate.decision.upper()}**",
        f"- Defense promotable: **{str(gate.promotable).lower()}**",
        "- Human review: **required before release**",
        "- Basis: observed campaign, JudgeAgent, replay, and benign evidence only.",
        "",
        "## Gate Summary",
    ]
    lines.extend(f"- {name}: {'pass' if passed else 'fail'}" for name, passed in gate.gates.items())
    lines.extend(["", "## Strategy Evidence"])
    lines.extend(
        f"- {item.strategy_id}: status={item.status}; evidence={', '.join(item.evidence_labels) or 'unknown'}; "
        f"live_judge={str(item.live_judge).lower()}; replay={str(item.replay_passed).lower()}; "
        f"benign={str(item.benign_replay_passed).lower()}"
        for item in result.strategies
    )
    if gate.reasons:
        lines.extend(["", "## Decision Reasons", *[f"- {reason}" for reason in gate.reasons]])
    lines.extend(["", "## Unknowns", *[f"- {unknown}" for unknown in gate.unknowns]])
    lines.extend(["", "## Findings"])
    for item in result.strategies:
        lines.append(
            f"- {item.strategy_id}: {item.finding_count} reported finding(s); "
            f"{item.high_finding_count} high severity"
        )
    return "\n".join(lines) + "\n"


__all__ = ["build_sanitized_packet", "render_executive_markdown"]
