"""Runtime summary helpers for orchestration truth surfaces."""

from typing import Any

from redthread.orchestration.canary_flow import CanaryPropagationReport

RuntimeSummary = dict[str, Any]


def _build_agentic_security_summary(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "action_total": state.get("agentic_action_total", 0),
        "authorization_decision_counts": state.get("authorization_decision_counts", {}),
        "canary_event_total": state.get("canary_event_total", 0) + state.get("live_canary_event_total", 0),
        "canary_report": state.get("canary_report", {}),
        "live_canary_event_total": state.get("live_canary_event_total", 0),
        "live_canary_report": state.get("live_canary_report", {}),
        "amplification_metrics": state.get("amplification_metrics", {}),
        "budget_stop_triggered": state.get("budget_stop_triggered", False),
        "untrusted_lineage_action_total": state.get("untrusted_lineage_action_total", 0),
    }


def merge_canary_reports(reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge worker canary reports into one prompt-safe summary."""
    typed = [CanaryPropagationReport.model_validate(report) for report in reports if report]
    if not typed:
        return {}
    crossed: list[str] = []
    for report in typed:
        for boundary in report.crossed_boundaries:
            if boundary not in crossed:
                crossed.append(boundary)
    first_blocked = next((report.first_blocked_point for report in typed if report.first_blocked_point), None)
    reached_execution = any(report.reached_execution_boundary for report in typed)
    contained = any(report.contained for report in typed) and not any(
        report.reached_execution_boundary and not report.contained for report in typed
    )
    return CanaryPropagationReport(
        injection_point=crossed[0] if crossed else None,
        crossed_boundaries=crossed,
        stage_count=len(crossed),
        first_blocked_point=first_blocked,
        reached_execution_boundary=reached_execution,
        contained=contained,
    ).model_dump(mode="json")


def merge_live_canary_report(summary: RuntimeSummary, execution_records: list[Any]) -> RuntimeSummary:
    """Merge canary containment decisions from live execution records."""
    decisions = [
        record.metadata.get("canary_containment")
        for record in execution_records
        if getattr(record, "metadata", None) and record.metadata.get("canary_containment")
    ]
    tagged = [decision for decision in decisions if decision.get("canary_tags")]
    if not tagged:
        return summary
    blocked = [decision for decision in tagged if decision.get("decision") == "block"]
    crossed = []
    for decision in tagged:
        seam = decision.get("seam")
        if seam and seam not in crossed:
            crossed.append(seam)
    live_report = CanaryPropagationReport(
        injection_point=crossed[0] if crossed else None,
        crossed_boundaries=crossed,
        stage_count=len(crossed),
        first_blocked_point=blocked[0].get("blocked_point") if blocked else None,
        reached_execution_boundary=any(d.get("boundary") == "execution_boundary" for d in tagged),
        contained=bool(blocked) or not any(d.get("boundary") == "execution_boundary" for d in tagged),
    ).model_dump(mode="json")
    merged = dict(summary)
    agentic = dict(merged.get("agentic_security", {}))
    agentic["live_canary_event_total"] = sum(len(d.get("canary_tags", [])) for d in tagged)
    agentic["live_canary_report"] = live_report
    agentic["canary_event_total"] = agentic.get("canary_event_total", 0) + agentic["live_canary_event_total"]
    merged["agentic_security"] = agentic
    return merged


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
