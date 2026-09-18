"""Proof-based launch gate decisions."""

from __future__ import annotations

from typing import Literal

from .models import LaunchGateSummary, LaunchReadinessConfig, StrategyReadiness


def build_launch_gate(
    reports: list[StrategyReadiness],
    policy: LaunchReadinessConfig,
) -> LaunchGateSummary:
    """Return a conservative decision from observed strategy evidence."""
    reasons: list[str] = []
    gates: dict[str, bool] = {}
    complete = all(item.status == "complete" for item in reports)
    gates["all_required_strategies_complete"] = complete
    if not complete:
        missing = ", ".join(item.strategy_id for item in reports if item.status != "complete")
        reasons.append(f"required strategy evidence incomplete: {missing}")
    live = all(item.live_judge for item in reports)
    gates["live_judge"] = live
    if policy.require_live_judge and not live:
        reasons.append("required live JudgeAgent evidence is absent")
    replay = all(item.replay_passed for item in reports)
    benign = all(item.benign_replay_passed for item in reports)
    gates["replay"] = replay
    gates["benign_replay"] = benign
    if policy.require_replay and not replay:
        reasons.append("required exploit replay evidence is absent or failed")
    if policy.require_benign_replay and not benign:
        reasons.append("required benign replay evidence is absent or failed")
    high = sum(item.high_finding_count for item in reports)
    gates["high_findings_within_limit"] = high <= policy.max_unresolved_high_findings
    if not gates["high_findings_within_limit"]:
        reasons.append(f"unresolved high findings: {high} (limit {policy.max_unresolved_high_findings})")
    fallback = any(item.fallback_evidence for item in reports)
    gates["no_fallback_evidence"] = not fallback
    if fallback and policy.fallback_diagnostic_only:
        reasons.append("fallback evidence is diagnostic-only and non-promotable")
    hard_block = not complete or (policy.require_live_judge and not live) or (
        policy.require_replay and not replay
    ) or (policy.require_benign_replay and not benign) or not gates["high_findings_within_limit"]
    if hard_block:
        decision: Literal["ready", "conditional", "blocked"] = "blocked"
    elif fallback:
        decision = "conditional"
    else:
        decision = "ready"
    return LaunchGateSummary(
        decision=decision,
        promotable=False,
        gates=gates,
        reasons=reasons,
        unresolved_high_findings=high,
        unknowns=[
            "scope uplift is unknown; this decision covers observed campaign scope only",
            "capability uplift is unknown; scores do not establish universal safety",
        ],
    )


__all__ = ["build_launch_gate"]
