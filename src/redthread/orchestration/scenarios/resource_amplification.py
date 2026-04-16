"""Resource amplification scenario simulation for Phase 8B."""

from __future__ import annotations

from redthread.orchestration.models import AgenticSecurityThreat, AmplificationMetrics


def run_resource_amplification_scenario(repair_loops: int = 3) -> dict[str, object]:
    tool_calls = repair_loops + 1
    metrics = AmplificationMetrics(
        tool_call_count=tool_calls,
        retry_count=repair_loops,
        duplicate_call_count=max(repair_loops - 1, 0),
        loop_depth=repair_loops,
        fallback_count=1 if repair_loops >= 2 else 0,
        token_growth_ratio=1.0 + (repair_loops * 1.8),
        budget_breached=repair_loops >= 3,
    )
    return {
        "threat": AgenticSecurityThreat.RESOURCE_AMPLIFICATION.value,
        "repair_loops": repair_loops,
        "amplification_metrics": metrics.model_dump(mode="json"),
    }
