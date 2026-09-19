"""AttackGraph — LangGraph worker node for executing attack algorithms.

Each AttackGraph instance runs ONE persona through the configured algorithm
(PAIR, TAP, Crescendo, or MCTS) in an isolated context, so multiple can be
fanned-out in parallel by the supervisor via LangGraph's Send API.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from typing_extensions import TypedDict

from redthread.models import AttackOutcome, AttackResult, AttackTrace, JudgeVerdict, Persona

logger = logging.getLogger(__name__)


class AttackWorkerState(TypedDict):
    """State schema for a single attack worker node."""

    settings_dict: dict[str, Any]
    persona_dict: dict[str, Any]
    target_system_prompt: str
    rubric_name: str
    result_dict: dict[str, Any] | None
    error: str | None


def _timeout_result(persona: Persona, algorithm: str, rubric_name: str) -> AttackResult:
    """Build an explicit failed result when a worker is cancelled by its deadline."""
    trace = AttackTrace(
        persona=persona,
        algorithm=algorithm,
        outcome=AttackOutcome.ERROR,
        metadata={"worker_status": "worker_timeout", "worker_error": "worker_timeout"},
    )
    verdict = JudgeVerdict(
        score=0.0,
        raw_score=0,
        reasoning="Attack worker timed out before producing a result.",
        feedback="",
        rubric_name=rubric_name,
        is_jailbreak=False,
    )
    return AttackResult(
        trace=trace,
        verdict=verdict,
        iterations_used=0,
        duration_seconds=0.0,
    )


async def run_attack_worker(state: AttackWorkerState) -> AttackWorkerState:
    """Executes a single attack run for one persona.

    Called by the LangGraph supervisor as a worker node. Deserializes inputs,
    dispatches to the appropriate algorithm, and serializes the result back
    into state for collection by the supervisor's collector node.
    """

    from redthread.config.settings import RedThreadSettings

    try:
        settings = RedThreadSettings.model_validate(state["settings_dict"])
        persona = Persona.model_validate(state["persona_dict"])

        logger.info(
            "⚔️  AttackWorker | persona=%s | algorithm=%s",
            persona.name,
            settings.algorithm.value,
        )

        from redthread.core.attack_runner import build_default_attack_runner_registry

        attacker = build_default_attack_runner_registry().create(settings.algorithm, settings)

        try:
            result = await asyncio.wait_for(
                attacker.run(
                    persona=persona,
                    target_system_prompt=state.get("target_system_prompt", ""),
                    rubric_name=state["rubric_name"],
                ),
                timeout=settings.worker_timeout_seconds,
            )
        except TimeoutError:
            logger.warning(
                "AttackWorker timed out after %.2fs: persona=%s",
                settings.worker_timeout_seconds,
                persona.name,
            )
            timeout_result = _timeout_result(
                persona,
                settings.algorithm.value,
                state["rubric_name"],
            )
            return {
                **state,
                "result_dict": timeout_result.model_dump(mode="json"),
                "error": "worker_timeout",
            }

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
