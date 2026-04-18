from __future__ import annotations

from redthread.models import MitreAtlasTactic
from redthread.orchestration.models import (
    ActionEffect,
    ActionEnvelope,
    ProvenanceRecord,
    ProvenanceSourceKind,
    TrustLevel,
)


def build_persona_generation_action(
    *,
    tactic: MitreAtlasTactic,
    technique_id: str,
) -> ActionEnvelope:
    return ActionEnvelope(
        actor_id=f"persona-generator-{tactic.value}",
        actor_role="attacker",
        capability="attacker.persona.generate",
        tool_name="attacker.persona.generate",
        arguments={"tactic": tactic.value, "technique_id": technique_id},
        target_sensitivity="low",
        provenance=ProvenanceRecord(
            source_kind=ProvenanceSourceKind.INTERNAL_AGENT,
            trust_level=TrustLevel.TRUSTED,
            origin_id=f"persona-generator-{tactic.value}",
        ),
        requested_effect=ActionEffect.EXECUTE,
    )
