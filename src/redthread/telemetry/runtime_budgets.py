"""Runtime budget evaluation helpers for agentic-security loops."""

from __future__ import annotations

from pydantic import BaseModel

from redthread.orchestration.models import AmplificationMetrics


class RuntimeBudgetThresholds(BaseModel):
    max_tool_calls: int = 4
    max_retries: int = 2
    max_token_growth_ratio: float = 5.0


def evaluate_runtime_budget(
    metrics: AmplificationMetrics,
    thresholds: RuntimeBudgetThresholds | None = None,
) -> dict[str, object]:
    threshold = thresholds or RuntimeBudgetThresholds()
    breaches: list[str] = []
    if metrics.tool_call_count > threshold.max_tool_calls:
        breaches.append("tool_call_count")
    if metrics.retry_count > threshold.max_retries:
        breaches.append("retry_count")
    if metrics.token_growth_ratio > threshold.max_token_growth_ratio:
        breaches.append("token_growth_ratio")
    return {
        "stop_triggered": bool(breaches) or metrics.budget_breached,
        "breaches": breaches,
        "thresholds": threshold.model_dump(mode="json"),
    }
