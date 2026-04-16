"""Runtime summary helpers for orchestration truth surfaces."""

from typing import Any

RuntimeSummary = dict[str, Any]


def _build_agentic_security_summary(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "action_total": state.get("agentic_action_total", 0),
        "authorization_decision_counts": state.get("authorization_decision_counts", {}),
        "canary_event_total": state.get("canary_event_total", 0),
        "amplification_metrics": state.get("amplification_metrics", {}),
        "untrusted_lineage_action_total": state.get("untrusted_lineage_action_total", 0),
    }


def build_runtime_summary(state: dict[str, Any]) -> RuntimeSummary:
    """Build a compact operator-facing runtime summary from supervisor state."""
    attack_worker_total = state.get("attack_worker_total", 0)
    attack_worker_failures = state.get("attack_worker_failures", 0)
    judge_worker_total = state.get("judge_worker_total", 0)
    judge_worker_failures = state.get("judge_worker_failures", 0)
    defense_worker_total = state.get("defense_worker_total", 0)
    defense_worker_failures = state.get("defense_worker_failures", 0)
    defense_deployments = state.get("defense_deployments", 0)
    error_count = len(state.get("errors", []))

    degraded_runtime = any(
        count > 0
        for count in (
            attack_worker_failures,
            judge_worker_failures,
            defense_worker_failures,
        )
    )

    return {
        "attack_worker_total": attack_worker_total,
        "attack_worker_failures": attack_worker_failures,
        "judge_worker_total": judge_worker_total,
        "judge_worker_failures": judge_worker_failures,
        "defense_worker_total": defense_worker_total,
        "defense_worker_failures": defense_worker_failures,
        "defense_deployments": defense_deployments,
        "degraded_runtime": degraded_runtime,
        "error_count": error_count,
        "error_samples": state.get("errors", [])[:3],
        "agentic_security": _build_agentic_security_summary(state),
    }
