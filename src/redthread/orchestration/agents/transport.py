"""Shared transport seam for specialized agent turns."""

from __future__ import annotations

from typing import Any

from redthread.core.attack_execution import attack_execution_metadata
from redthread.orchestration.agents.models import AgentPhaseState
from redthread.pyrit_adapters.targets import send_with_execution_metadata


async def send_agent_message(
    target: Any,
    *,
    prompt: str,
    state: AgentPhaseState,
    lane: str,
    conversation_id: str,
) -> str:
    """Send one chain turn through the shared execution and canary seam."""
    metadata = state.get("metadata", {})
    trace_id = metadata.get("trace_id", "specialized")
    if lane in {"target.social", "target.exploit"}:
        conversation_id = metadata.get(
            "target_conversation_id", f"{trace_id}:target"
        )
    else:
        conversation_id = f"{trace_id}:{conversation_id}"
    return await send_with_execution_metadata(
        target,
        prompt=prompt,
        conversation_id=conversation_id,
        execution_metadata=attack_execution_metadata(
            algorithm="agent_chain",
            lane=lane,
            trace_id=trace_id,
        ),
    )
