"""Typed data structures and state schemas for specialized agent nodes."""

from __future__ import annotations

from typing import Any

from typing_extensions import TypedDict


class AgentPhaseState(TypedDict, total=False):
    """State schema flowing through the specialized agent subgraphs."""

    persona_dict: dict[str, Any]
    target_system_prompt: str
    recon_findings: list[str]
    social_pretext: str
    exploit_payload: str
    turns: list[dict[str, Any]]
    current_phase: str
    is_jailbreak: bool
    metadata: dict[str, Any]
    error: str | None
    phase_errors: list[dict[str, str]]


class AgentNodeResult(TypedDict, total=False):
    """Standard output schema for an individual specialized agent node."""

    agent_name: str
    phase: str
    success: bool
    output: str
    findings: list[str]
    metadata: dict[str, Any]


async def send_agent_message(
    target: Any,
    *,
    prompt: str,
    state: AgentPhaseState,
    lane: str,
    conversation_id: str,
) -> str:
    """Send one chain turn through the shared execution and canary seam."""
    from redthread.core.attack_execution import attack_execution_metadata
    from redthread.pyrit_adapters.targets import send_with_execution_metadata

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
