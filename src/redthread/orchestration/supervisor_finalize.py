"""Campaign finalization node for the RedThread supervisor graph."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from redthread.models import AttackResult, CampaignConfig, CampaignResult, Persona
from redthread.orchestration.supervisor_state import SupervisorState

logger = logging.getLogger(__name__)


async def finalize_node(state: SupervisorState) -> dict[str, Any]:
    """Assemble the final CampaignResult from judged results."""
    from redthread.orchestration.runtime_summary import build_runtime_summary
    from redthread.personas.outcomes import build_persona_outcome_telemetry, persona_profiles_by_id
    from redthread.personas.prompt_layers import PromptingLayerProfile

    config = CampaignConfig.model_validate(state["config_dict"])
    results = [AttackResult.model_validate(raw) for raw in state["judged_results"]]
    personas = [Persona.model_validate(raw) for raw in state["persona_dicts"]]
    profile = (
        PromptingLayerProfile.model_validate(config.prompting_layer_profile)
        if config.prompting_layer_profile else None
    )
    telemetry = build_persona_outcome_telemetry(results, persona_profiles_by_id(personas, profile))
    runtime_summary = build_runtime_summary(state)
    ended_at = datetime.now(timezone.utc)
    started_at_raw = state.get("campaign_started_at")
    started_at = datetime.fromisoformat(started_at_raw) if started_at_raw else ended_at
    campaign = CampaignResult(
        config=config,
        results=results,
        started_at=started_at,
        ended_at=ended_at,
        metadata={
            "runtime_summary": runtime_summary,
            "agentic_security_report": state.get("agentic_security_report", {}),
            "degraded_runtime": runtime_summary["degraded_runtime"],
            "error_count": runtime_summary["error_count"],
            "persona_outcome_telemetry": telemetry.model_dump(mode="json"),
            "defense_records": state.get("defense_records", []),
        },
    )
    logger.info(
        "✅ Supervisor finalized | runs=%d | degraded=%s",
        len(campaign.results),
        runtime_summary["degraded_runtime"],
    )
    return {"campaign_result_dict": campaign.model_dump(mode="json")}


__all__ = ["finalize_node"]
