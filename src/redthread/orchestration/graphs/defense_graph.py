"""DefenseGraph — LangGraph worker node for post-evaluation defense synthesis.

Receives a judged AttackResult, passes it through the DefenseSynthesisEngine
(Isolate → Classify → Generate → Validate → Deploy), and writes validated
guardrail records to MEMORY.md via MemoryIndex.

Only called for confirmed jailbreaks (is_jailbreak=True from JudgeWorker).
"""

from __future__ import annotations

import logging
from typing import Any

from typing_extensions import TypedDict

logger = logging.getLogger(__name__)


# ── Worker state ──────────────────────────────────────────────────────────────

class DefenseWorkerState(TypedDict):
    """State schema for the defense synthesis worker node."""

    settings_dict: dict[str, Any]           # Serialized RedThreadSettings
    result_dict: dict[str, Any]             # Serialized (judged) AttackResult
    defense_deployed: bool                  # True if guardrail was validated + indexed
    guardrail_clause: str | None            # The deployed clause (if successful)
    error: str | None


# ── Worker node function ──────────────────────────────────────────────────────

async def run_defense_worker(state: DefenseWorkerState) -> DefenseWorkerState:
    """Runs the 5-step Defense Synthesis pipeline and indexes valid guardrails.

    Called by the LangGraph supervisor only for confirmed jailbreaks.
    """
    from redthread.config.settings import RedThreadSettings
    from redthread.core.defense_synthesis import DefenseSynthesisEngine
    from redthread.memory.index import MemoryIndex
    from redthread.models import AttackResult

    try:
        settings = RedThreadSettings.model_validate(state["settings_dict"])
        result = AttackResult.model_validate(state["result_dict"])

        logger.info(
            "🛡️  DefenseWorker | trace=%s | synthesizing guardrail...",
            result.trace.id,
        )

        engine = DefenseSynthesisEngine(settings)
        record = await engine.run(result)

        if record.validation.passed:
            index = MemoryIndex(settings)
            index.append(record)
            logger.info(
                "✅ DefenseWorker | guardrail deployed | trace=%s | category=%s",
                record.trace_id,
                record.classification.category,
            )
            return {
                **state,
                "defense_deployed": True,
                "guardrail_clause": record.guardrail_clause,
                "error": None,
            }
        else:
            logger.warning(
                "⚠️  DefenseWorker | validation failed | trace=%s | replay_score=%.2f",
                record.trace_id,
                record.validation.judge_score,
            )
            return {
                **state,
                "defense_deployed": False,
                "guardrail_clause": record.guardrail_clause,  # Still return clause for inspection
                "error": None,
            }

    except Exception as exc:
        logger.exception("DefenseWorker failed: %s", exc)
        return {
            **state,
            "defense_deployed": False,
            "guardrail_clause": None,
            "error": str(exc),
        }
