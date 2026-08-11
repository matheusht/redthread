"""LangGraph supervisor facade for RedThread campaigns.

The public import surface stays here for compatibility. The graph is now built
from small stage modules so the supervisor file remains an auditable facade.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from redthread.config.settings import RedThreadSettings
from redthread.core.defense_status import validated_candidate_count_fields
from redthread.models import CampaignConfig, CampaignResult
from redthread.orchestration.supervisor_finalize import finalize_node
from redthread.orchestration.supervisor_graph import attack_worker_node, build_supervisor_graph
from redthread.orchestration.supervisor_nodes import (
    _worker_canary_update,
    analyze_agentic_security_node,
    collect_results_node,
    defense_synthesis_node,
    generate_personas_node,
    judge_all_results_node,
)
from redthread.orchestration.supervisor_routing import fan_out_attack_workers, route_to_defense
from redthread.orchestration.supervisor_state import SupervisorState

logger = logging.getLogger(__name__)


class RedThreadSupervisor:
    """Facade over the compiled LangGraph supervisor graph."""

    def __init__(self, settings: RedThreadSettings) -> None:
        self.settings = settings
        self._graph = build_supervisor_graph().compile()

    async def invoke(self, config: CampaignConfig) -> CampaignResult:
        """Execute the full campaign via the LangGraph supervisor."""
        from redthread.core.guardrail_loader import GuardrailLoader

        loader = GuardrailLoader(self.settings)
        injected_config = loader.inject_guardrails(config)
        initial_state = _initial_state(self.settings, injected_config)
        logger.info(
            "🚀 Supervisor.invoke | objective=%s | algorithm=%s | personas=%d",
            config.objective,
            self.settings.algorithm.value,
            config.num_personas,
        )
        final_state = await self._graph.ainvoke(initial_state)
        if final_state.get("errors"):
            logger.warning(
                "Supervisor completed with %d error(s): %s",
                len(final_state["errors"]),
                final_state["errors"][:3],
            )
        if final_state.get("campaign_result_dict"):
            return CampaignResult.model_validate(final_state["campaign_result_dict"])
        return CampaignResult(config=injected_config, ended_at=datetime.now(timezone.utc))


def _initial_state(settings: RedThreadSettings, config: CampaignConfig) -> SupervisorState:
    """Build the initial graph state for one campaign."""
    return {
        "settings_dict": settings.model_dump(mode="json"),
        "config_dict": config.model_dump(mode="json"),
        "campaign_started_at": datetime.now(timezone.utc).isoformat(),
        "persona_dicts": [],
        "attack_results": [],
        "attack_worker_total": 0,
        "attack_worker_failures": 0,
        "judged_results": [],
        "judge_worker_total": 0,
        "judge_worker_failures": 0,
        "defense_records": [],
        "defense_worker_total": 0,
        "defense_worker_failures": 0,
        **validated_candidate_count_fields(0),
        "agentic_security_report": {},
        "agentic_action_total": 0,
        "authorization_decision_counts": {},
        "canary_event_total": 0,
        "canary_report": {},
        "live_canary_event_total": 0,
        "live_canary_report": {},
        "amplification_metrics": {},
        "budget_stop_triggered": False,
        "untrusted_lineage_action_total": 0,
        "campaign_result_dict": None,
        "errors": [],
    }


__all__ = [
    "RedThreadSupervisor",
    "SupervisorState",
    "_worker_canary_update",
    "analyze_agentic_security_node",
    "attack_worker_node",
    "build_supervisor_graph",
    "collect_results_node",
    "defense_synthesis_node",
    "fan_out_attack_workers",
    "finalize_node",
    "generate_personas_node",
    "judge_all_results_node",
    "route_to_defense",
]
