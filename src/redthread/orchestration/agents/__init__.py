"""Specialized adversarial agent nodes for reconnaissance, social engineering, and exploitation."""

from __future__ import annotations

from redthread.orchestration.agents.agent_chain import (
    build_specialized_agent_graph,
    run_specialized_pipeline,
)
from redthread.orchestration.agents.exploit_agent import ExploitAgent, exploit_agent_node
from redthread.orchestration.agents.models import AgentNodeResult, AgentPhaseState
from redthread.orchestration.agents.recon_agent import ReconAgent, recon_agent_node
from redthread.orchestration.agents.social_agent import SocialAgent, social_agent_node
from redthread.orchestration.agents.specialized_adapter import (
    SpecializedAttackRunner,
    run_specialized_attack,
)

__all__ = [
    "AgentNodeResult",
    "AgentPhaseState",
    "ExploitAgent",
    "ReconAgent",
    "SocialAgent",
    "SpecializedAttackRunner",
    "build_specialized_agent_graph",
    "exploit_agent_node",
    "recon_agent_node",
    "run_specialized_pipeline",
    "run_specialized_attack",
    "social_agent_node",
]
