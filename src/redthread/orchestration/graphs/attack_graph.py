"""AttackGraph — LangGraph worker node for executing attack algorithms.

Each AttackGraph instance runs ONE persona through the configured algorithm
(PAIR or TAP) in an isolated context, so multiple can be fanned-out in
parallel by the supervisor via LangGraph's Send API.
"""

from __future__ import annotations

import logging
from typing import Any

from typing_extensions import TypedDict

logger = logging.getLogger(__name__)


# ── Worker state ──────────────────────────────────────────────────────────────

class AttackWorkerState(TypedDict):
    """State schema for a single attack worker node."""

    settings_dict: dict[str, Any]       # Serialized RedThreadSettings
    persona_dict: dict[str, Any]        # Serialized Persona
    rubric_name: str
    result_dict: dict[str, Any] | None  # Serialized AttackResult (output)
    error: str | None


# ── Worker node function ──────────────────────────────────────────────────────

async def run_attack_worker(state: AttackWorkerState) -> AttackWorkerState:
    """Executes a single attack run (PAIR or TAP) for one persona.

    Called by the LangGraph supervisor as a worker node. Deserializes inputs,
    dispatches to the appropriate algorithm, and serializes the result back
    into state for collection by the supervisor's collector node.
    """
    import asyncio

    from redthread.config.settings import AlgorithmType, RedThreadSettings
    from redthread.models import Persona

    try:
        settings = RedThreadSettings.model_validate(state["settings_dict"])
        persona = Persona.model_validate(state["persona_dict"])

        logger.info(
            "⚔️  AttackWorker | persona=%s | algorithm=%s",
            persona.name,
            settings.algorithm.value,
        )

        if settings.algorithm == AlgorithmType.PAIR:
            from redthread.core.pair import PAIRAttack
            attacker = PAIRAttack(settings)
        elif settings.algorithm == AlgorithmType.TAP:
            from redthread.core.tap import TAPAttack
            attacker = TAPAttack(settings)
        else:
            raise NotImplementedError(
                f"Algorithm '{settings.algorithm}' not supported in AttackWorker."
            )

        result = await attacker.run(persona, rubric_name=state["rubric_name"])

        return {
            **state,
            "result_dict": result.model_dump(mode="json"),
            "error": None,
        }

    except Exception as exc:
        logger.exception("AttackWorker failed: %s", exc)
        return {
            **state,
            "result_dict": None,
            "error": str(exc),
        }
