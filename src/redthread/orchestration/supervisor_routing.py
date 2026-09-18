"""Routing helpers for the RedThread supervisor graph."""

from __future__ import annotations

import logging
from typing import Literal

from langgraph.types import Send

from redthread.orchestration.supervisor_state import SupervisorState

logger = logging.getLogger(__name__)


def fan_out_attack_workers(state: SupervisorState) -> list[Send]:
    """Fan out one attack worker per persona using LangGraph Send API."""
    from redthread.orchestration.graphs.attack_graph import AttackWorkerState

    config = state["config_dict"]
    sends = []
    algorithm = state["settings_dict"].get("algorithm")
    worker_node = "specialized_attack_worker" if algorithm == "agent_chain" else "attack_worker"
    for persona_dict in state["persona_dicts"]:
        worker_state: AttackWorkerState = {
            "settings_dict": state["settings_dict"],
            "persona_dict": persona_dict,
            "target_system_prompt": config.get("target_system_prompt", ""),
            "rubric_name": config.get("rubric_name", "authorization_bypass"),
            "result_dict": None,
            "error": None,
        }
        sends.append(Send(worker_node, worker_state))

    logger.info("⚡ Supervisor: fanning out %d attack workers...", len(sends))
    return sends


def route_to_defense(state: SupervisorState) -> Literal["defense_synthesis", "finalize"]:
    """Skip defense synthesis if no JudgeAgent-confirmed jailbreaks exist."""
    jailbreaks = [
        result for result in state["judged_results"]
        if result.get("verdict", {}).get("is_jailbreak")
    ]
    if jailbreaks:
        logger.info(
            "🛡️  Supervisor: routing to defense synthesis (%d jailbreaks).",
            len(jailbreaks),
        )
        return "defense_synthesis"
    logger.info("✅ Supervisor: no jailbreaks — routing directly to finalize.")
    return "finalize"


__all__ = ["fan_out_attack_workers", "route_to_defense"]
