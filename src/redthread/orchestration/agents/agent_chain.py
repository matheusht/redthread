"""Specialized agent chain graph — LangGraph orchestration for Recon -> Social -> Exploit."""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from redthread.orchestration.agents.exploit_agent import exploit_agent_node
from redthread.orchestration.agents.models import AgentPhaseState
from redthread.orchestration.agents.recon_agent import recon_agent_node
from redthread.orchestration.agents.social_agent import social_agent_node

logger = logging.getLogger(__name__)


def build_specialized_agent_graph() -> StateGraph[AgentPhaseState]:
    """Build LangGraph StateGraph linking Recon -> Social -> Exploit."""
    graph = StateGraph(AgentPhaseState)
    graph.add_node("recon", recon_agent_node)
    graph.add_node("social", social_agent_node)
    graph.add_node("exploit", exploit_agent_node)

    graph.set_entry_point("recon")
    graph.add_edge("recon", "social")
    graph.add_edge("social", "exploit")
    graph.add_edge("exploit", END)

    return graph


async def run_specialized_pipeline(
    state: AgentPhaseState,
    recon_agent: Any | None = None,
    social_agent: Any | None = None,
    exploit_agent: Any | None = None,
) -> AgentPhaseState:
    current: AgentPhaseState = state.copy()

    if recon_agent is None and social_agent is None and exploit_agent is None:
        from redthread.config.settings import RedThreadSettings
        from redthread.pyrit_adapters.targets import build_attacker, build_target

        settings = RedThreadSettings.model_validate(
            current.get("metadata", {}).get("settings_dict", {})
        )
        metadata = {
            **current.get("metadata", {}),
            "_shared_target": build_target(settings),
            "_shared_attacker": build_attacker(settings),
        }
        current = {**current, "metadata": metadata}

    if recon_agent is not None:
        current = await recon_agent.run(current)
    else:
        current = await recon_agent_node(current)

    if social_agent is not None:
        current = await social_agent.run(current)
    else:
        current = await social_agent_node(current)

    if exploit_agent is not None:
        current = await exploit_agent.run(current)
    else:
        current = await exploit_agent_node(current)

    return current
