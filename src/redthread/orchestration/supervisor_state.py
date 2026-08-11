"""State schema and reducers for the RedThread supervisor graph."""

from __future__ import annotations

from typing import Annotated, Any

from typing_extensions import TypedDict


def merge_lists(a: list[Any], b: list[Any]) -> list[Any]:
    """LangGraph reducer for fan-in list fields."""
    return a + b


class SupervisorState(TypedDict):
    """Global state flowing through the LangGraph supervisor."""

    settings_dict: dict[str, Any]
    config_dict: dict[str, Any]
    campaign_started_at: str
    persona_dicts: list[dict[str, Any]]

    attack_results: Annotated[list[dict[str, Any]], merge_lists]
    attack_worker_total: int
    attack_worker_failures: int

    judged_results: Annotated[list[dict[str, Any]], merge_lists]
    judge_worker_total: int
    judge_worker_failures: int

    defense_records: Annotated[list[dict[str, Any]], merge_lists]
    defense_worker_total: int
    defense_worker_failures: int
    defense_validated_candidates: int
    defense_deployments: int  # Deprecated alias for defense_validated_candidates.

    agentic_security_report: dict[str, Any]
    agentic_action_total: int
    authorization_decision_counts: dict[str, int]
    canary_event_total: int
    canary_report: dict[str, Any]
    live_canary_event_total: int
    live_canary_report: dict[str, Any]
    amplification_metrics: dict[str, Any]
    budget_stop_triggered: bool
    untrusted_lineage_action_total: int

    campaign_result_dict: dict[str, Any] | None
    errors: Annotated[list[str], merge_lists]


__all__ = ["SupervisorState", "merge_lists"]
