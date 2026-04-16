"""Sealed tool-attack scenario runner for Phase 8B."""

from __future__ import annotations

from redthread.orchestration.models import (
    ActionEffect,
    ActionEnvelope,
    AgenticSecurityThreat,
    BoundaryCrossing,
    BoundaryType,
    ProvenanceRecord,
    ProvenanceSourceKind,
    TrustLevel,
)
from redthread.tools.fixtures.agentic_security import ToolFixture
from redthread.tools.simulated_registry import SimulatedToolRegistry


def run_tool_attack_scenario(
    fixture: ToolFixture,
    *,
    arguments: dict[str, str],
    actor_id: str = "tool-worker",
) -> dict[str, object]:
    registry = SimulatedToolRegistry()
    registry.register(fixture)
    tool_response = registry.invoke(fixture["name"], arguments)

    provenance = ProvenanceRecord(
        source_kind=ProvenanceSourceKind.EXTERNAL_TOOL,
        trust_level=TrustLevel.UNTRUSTED,
        origin_id=fixture["name"],
        boundary_crossings=[
            BoundaryCrossing(boundary=BoundaryType.TOOL_RETURN, detail="tool output entered context")
        ],
        canary_tags=tool_response["canary_tags"],
        derived_from_untrusted=True,
    )
    requested_action = None
    if tool_response["suggested_capability"]:
        requested_action = ActionEnvelope(
            actor_id=actor_id,
            actor_role="tool_executor",
            capability=tool_response["suggested_capability"],
            tool_name=tool_response["suggested_capability"],
            arguments={"source_tool": fixture["name"]},
            target_sensitivity="high",
            provenance=provenance,
            requested_effect=ActionEffect.EXECUTE,
            canary_tags=tool_response["canary_tags"],
        ).model_dump(mode="json")

    return {
        "threat": AgenticSecurityThreat.TOOL_POISONING.value,
        "tool_response": tool_response,
        "poisoned": bool(tool_response["suggested_capability"]),
        "requested_action": requested_action,
    }
