"""LangGraph construction for the RedThread supervisor."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from redthread.orchestration.supervisor_finalize import finalize_node
from redthread.orchestration.supervisor_nodes import (
    analyze_agentic_security_node,
    collect_results_node,
    defense_synthesis_node,
    generate_personas_node,
    judge_all_results_node,
)
from redthread.orchestration.supervisor_routing import fan_out_attack_workers, route_to_defense
from redthread.orchestration.supervisor_state import SupervisorState


async def attack_worker_node(state: Any) -> dict[str, Any]:
    """Adapter wrapping run_attack_worker for LangGraph node registration."""
    from redthread.orchestration.graphs.attack_graph import run_attack_worker

    result = await run_attack_worker(state)  # type: ignore[arg-type]
    return {"attack_results": [result]}


async def specialized_attack_worker_node(state: Any) -> dict[str, Any]:
    """Adapter wrapping the specialized chain worker for graph registration."""
    from redthread.orchestration.graphs.attack_graph import run_specialized_attack_worker

    result = await run_specialized_attack_worker(state)  # type: ignore[arg-type]
    return {"attack_results": [result]}


def build_supervisor_graph() -> StateGraph[SupervisorState]:
    """Construct the LangGraph supervisor StateGraph."""
    graph = StateGraph(SupervisorState)
    graph.add_node("generate_personas", generate_personas_node)
    graph.add_node("attack_worker", attack_worker_node)
    graph.add_node("specialized_attack_worker", specialized_attack_worker_node)
    graph.add_node("collect_results", collect_results_node)
    graph.add_node("judge_all", judge_all_results_node)
    graph.add_node("analyze_agentic_security", analyze_agentic_security_node)
    graph.add_node("defense_synthesis", defense_synthesis_node)
    graph.add_node("finalize", finalize_node)
    graph.set_entry_point("generate_personas")
    graph.add_conditional_edges(
        "generate_personas",
        fan_out_attack_workers,
        ["attack_worker", "specialized_attack_worker"],
    )
    graph.add_edge("attack_worker", "collect_results")
    graph.add_edge("specialized_attack_worker", "collect_results")
    graph.add_edge("collect_results", "judge_all")
    graph.add_edge("judge_all", "analyze_agentic_security")
    graph.add_conditional_edges(
        "analyze_agentic_security",
        route_to_defense,
        {"defense_synthesis": "defense_synthesis", "finalize": "finalize"},
    )
    graph.add_edge("defense_synthesis", "finalize")
    graph.add_edge("finalize", END)
    return graph


__all__ = [
    "attack_worker_node",
    "build_supervisor_graph",
    "specialized_attack_worker_node",
]
