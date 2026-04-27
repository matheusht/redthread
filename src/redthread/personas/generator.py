"""PersonaGenerator — LLM-driven adversarial profile creation."""

from __future__ import annotations

import logging
from typing import Any, cast

from redthread.config.settings import RedThreadSettings
from redthread.models import MitreAtlasTactic, Persona, PsychologicalTrigger
from redthread.personas.generation_defaults import (
    build_dry_run_persona,
    default_trigger_sets,
    get_primary_technique,
)
from redthread.personas.generation_support import (
    PERSONA_GENERATION_PROMPT,
    normalize_persona_data,
    parse_persona_json,
    render_prompting_layer_constraints,
)
from redthread.personas.prompt_layers import PromptingLayerProfile
from redthread.pyrit_adapters.targets import (
    ExecutionMetadata,
    ExecutionRecorder,
    RedThreadTarget,
    send_with_execution_metadata,
)

logger = logging.getLogger(__name__)


class PersonaGenerator:
    """Generates adversarial personas using the attacker LLM."""

    def __init__(
        self,
        settings: RedThreadSettings,
        execution_recorder: ExecutionRecorder | None = None,
    ) -> None:
        self.settings = settings
        self._execution_recorder = execution_recorder
        self._attacker: RedThreadTarget | None = None

    def _get_attacker(self) -> RedThreadTarget:
        if self._attacker is None:
            from redthread.pyrit_adapters.targets import build_attacker

            self._attacker = build_attacker(
                self.settings,
                execution_recorder=self._execution_recorder,
            )
        return self._attacker

    async def generate(
        self,
        objective: str,
        tactic: MitreAtlasTactic = MitreAtlasTactic.INITIAL_ACCESS,
        triggers: list[PsychologicalTrigger] | None = None,
        prompting_layer_profile: PromptingLayerProfile | None = None,
    ) -> Persona:
        if triggers is None:
            triggers = [PsychologicalTrigger.AUTHORITY, PsychologicalTrigger.URGENCY]
        if self.settings.dry_run:
            return build_dry_run_persona(objective, tactic, triggers, prompting_layer_profile)

        technique = get_primary_technique(tactic)
        prompt = PERSONA_GENERATION_PROMPT.format(
            tactic_name=tactic.name.replace("_", " ").title(),
            tactic_id=tactic.value,
            technique_name=technique.name,
            technique_id=technique.id,
            technique_description=technique.description,
            objective=objective,
            triggers=", ".join(trigger.value for trigger in triggers),
            prompting_layer_constraints=render_prompting_layer_constraints(prompting_layer_profile),
        )
        logger.info("Generating persona", extra={"tactic": tactic.value, "technique": technique.id})
        return await self._generate_with_retries(prompt, tactic, triggers, technique.id, technique.name)

    async def generate_batch(
        self,
        objective: str,
        count: int = 3,
        tactics: list[MitreAtlasTactic] | None = None,
        prompting_layer_profile: PromptingLayerProfile | None = None,
    ) -> list[Persona]:
        if tactics is None:
            default_tactics = [
                MitreAtlasTactic.INITIAL_ACCESS,
                MitreAtlasTactic.EXFILTRATION,
                MitreAtlasTactic.ML_ATTACK_STAGING,
            ]
            tactics = (default_tactics * ((count // len(default_tactics)) + 1))[:count]
        personas = []
        for index, tactic in enumerate(tactics[:count]):
            trigger_sets = default_trigger_sets()
            triggers = trigger_sets[index % len(trigger_sets)]
            persona = await self.generate(
                objective,
                tactic,
                triggers,
                prompting_layer_profile,
            )
            personas.append(persona)
            logger.info("Generated persona %d/%d: %s", index + 1, count, persona.name)
        return personas

    def _parse_persona_json(self, raw: str) -> dict[str, Any]:
        return parse_persona_json(raw)

    def _normalize_persona_data(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        return normalize_persona_data(raw_data)

    async def _generate_with_retries(
        self,
        prompt: str,
        tactic: MitreAtlasTactic,
        triggers: list[PsychologicalTrigger],
        technique_id: str,
        technique_name: str,
    ) -> Persona:
        from redthread.core.mcts_helpers import derive_strategies
        from redthread.personas.live_authorization import build_persona_generation_action

        action = build_persona_generation_action(tactic=tactic, technique_id=technique_id)
        for attempt in range(3):
            raw_response = await send_with_execution_metadata(
                self._get_attacker(),
                prompt=prompt,
                execution_metadata=ExecutionMetadata(
                    seam="persona.generate",
                    role="attacker",
                    evidence_class="live_generation",
                    metadata={
                        "tactic": tactic.value,
                        "technique_id": technique_id,
                        "authorization_action": action,
                    },
                ),
            )
            try:
                persona_data = self._normalize_persona_data(self._parse_persona_json(raw_response))
                strategies = persona_data.get("allowed_strategies", [])
                if not isinstance(strategies, list):
                    strategies = []
                candidate = Persona(
                    name=cast(str, persona_data["name"]),
                    tactic=tactic,
                    technique=f"{technique_id} — {technique_name}",
                    cover_story=cast(str, persona_data["cover_story"]),
                    hidden_objective=cast(str, persona_data["hidden_objective"]),
                    system_prompt=cast(str, persona_data["system_prompt"]),
                    psychological_triggers=triggers,
                    allowed_strategies=strategies,
                )
                if not candidate.allowed_strategies:
                    candidate.allowed_strategies = derive_strategies(candidate)
                return candidate
            except (ValueError, KeyError) as exc:
                logger.warning(
                    "Persona generation attempt %d failed: %s | raw=%s",
                    attempt + 1,
                    exc,
                    raw_response[:300].replace("\n", " "),
                )
                if attempt == 2:
                    raise
        raise RuntimeError("persona generation retries exhausted")
