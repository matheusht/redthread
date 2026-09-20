"""Crescendo — Multi-Turn Conversational Escalation attack algorithm.

Implements the "foot-in-the-door" escalation technique from:
  "Crescendo: A Context-Window Escalation Attack on LLMs" (2024)
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from redthread.config.settings import RedThreadSettings
from redthread.core.attack_execution import attack_execution_metadata
from redthread.core.crescendo_prompts import (
    build_retry_prompt,
    build_turn_prompt,
    compile_target_prompt,
    finalize_crescendo_trace,
    format_history,
    resolve_crescendo_system_prompt,
)
from redthread.core.mcts_helpers import derive_strategies
from redthread.core.narrative_models import NarrativeGuidance, NarrativeState
from redthread.core.narrative_policy import NarrativeAdaptationPolicy
from redthread.evaluation.judge import JudgeAgent
from redthread.models import (
    AttackResult,
    AttackTrace,
    ConversationTurn,
    CrescendoTurn,
    Persona,
)
from redthread.pyrit_adapters.targets import (
    RedThreadTarget,
    build_attacker,
    build_target,
    send_with_execution_metadata,
)

logger = logging.getLogger(__name__)


class CrescendoAttack:
    """Crescendo multi-turn conversational escalation attack."""

    def __init__(
        self,
        settings: RedThreadSettings,
        attacker: RedThreadTarget | None = None,
        target: RedThreadTarget | None = None,
        judge: JudgeAgent | None = None,
    ) -> None:
        self.settings = settings
        self._attacker = attacker
        self._target = target
        self._judge = judge or JudgeAgent(settings)

    def _get_attacker(self) -> RedThreadTarget:
        if self._attacker is None:
            self._attacker = build_attacker(self.settings)
        return self._attacker

    def _get_target(self) -> RedThreadTarget:
        if self._target is None:
            self._target = build_target(self.settings)
        return self._target

    async def run(
        self,
        persona: Persona,
        target_system_prompt: str = "",
        rubric_name: str = "authorization_bypass",
    ) -> AttackResult:
        """Execute the full Crescendo escalation loop for a given persona."""
        start_time = time.monotonic()
        trace = AttackTrace(
            persona=persona,
            algorithm="crescendo",
            started_at=datetime.now(timezone.utc),
            metadata={"target_system_prompt": target_system_prompt} if target_system_prompt else {},
        )
        logger.info(
            "🔴 Crescendo attack starting | persona=%s | target=%s | max_turns=%d",
            persona.name,
            self.settings.target_model,
            self.settings.crescendo_max_turns,
        )
        attacker_system = resolve_crescendo_system_prompt(persona, self.settings)
        history: list[tuple[str, str]] = []
        escalation_level = 0
        narrative_state = NarrativeState()
        narrative_policy = NarrativeAdaptationPolicy(
            strategies=derive_strategies(persona, use_cop=self.settings.use_cop),
        ) if self.settings.narrative_adaptation_enabled else None

        for turn_num in range(1, self.settings.crescendo_max_turns + 1):
            if self.settings.dry_run:
                logger.info("🟡 Dry run — skipping target interaction")
                break

            guidance: NarrativeGuidance | None = (
                narrative_policy.recommend(narrative_state) if narrative_policy else None
            )
            accepted: CrescendoTurn | None = None

            for attempt in range(1, self.settings.crescendo_backtrack_limit + 2):
                is_retry = attempt > 1
                history_text = format_history(history)
                if not is_retry:
                    prompt_input = build_turn_prompt(
                        history_text, escalation_level, turn_num,
                        self.settings.crescendo_max_turns, persona.hidden_objective,
                        is_first=(turn_num == 1), guidance=guidance,
                    )
                else:
                    last_score = trace.crescendo_turns[-1].score if trace.crescendo_turns else 0.0
                    prompt_input = build_retry_prompt(
                        history_text, escalation_level, turn_num,
                        self.settings.crescendo_backtrack_limit, persona.hidden_objective,
                        attempt, last_score, guidance=guidance,
                    )

                logger.debug("🤖 Attacker generating turn %d (attempt %d)…", turn_num, attempt)
                attacker_msg = (await send_with_execution_metadata(
                    self._get_attacker(),
                    prompt=f"[SYSTEM]: {attacker_system}\n\n[USER]: {prompt_input}",
                    conversation_id=f"cres-attacker-{trace.id}",
                    execution_metadata=attack_execution_metadata(
                        algorithm="crescendo", lane="attacker", trace_id=trace.id,
                        metadata={"turn": turn_num, "attempt": attempt},
                    ),
                )).strip()

                target_prompt = compile_target_prompt(history, attacker_msg)
                target_response = await send_with_execution_metadata(
                    self._get_target(),
                    prompt=target_prompt,
                    conversation_id=f"cres-target-{trace.id}-t{turn_num}",
                    execution_metadata=attack_execution_metadata(
                        algorithm="crescendo", lane="target", trace_id=trace.id,
                        metadata={"turn": turn_num, "attempt": attempt},
                    ),
                )
                score = self._judge.evaluate_turn_raw(attacker_msg, target_response, rubric_name)
                logger.info(
                    "⚖️  Turn %d/%d | attempt %d | score %.1f | level=%d",
                    turn_num, self.settings.crescendo_max_turns, attempt, score, escalation_level,
                )

                is_escalated = score >= self.settings.crescendo_escalation_threshold
                is_last = attempt > self.settings.crescendo_backtrack_limit
                if is_escalated or is_last:
                    accepted = CrescendoTurn(
                        turn_number=turn_num, escalation_level=escalation_level,
                        attacker_prompt=attacker_msg, target_response=target_response,
                        score=score, backtracked=is_retry, backtrack_attempts=attempt - 1,
                    )
                    if is_escalated:
                        history.append((attacker_msg, target_response))
                        escalation_level = min(escalation_level + 1, 5)
                    break

            if accepted:
                trace.crescendo_turns.append(accepted)
                trace.turns.append(ConversationTurn(
                    turn_number=turn_num,
                    attacker_prompt=accepted.attacker_prompt,
                    target_response=accepted.target_response,
                ))
                if narrative_policy is not None and guidance is not None:
                    narrative_state = narrative_policy.update(
                        state=narrative_state, score=accepted.score,
                        target_response=accepted.target_response,
                        strategy_used=guidance.recommended_strategy,
                    )
                if accepted.score >= self.settings.success_threshold:
                    logger.info("✅ Potential jailbreak at turn %d (score %.1f)", turn_num, accepted.score)
                    break

        if narrative_policy is not None:
            trace.metadata["narrative_state"] = narrative_state.model_dump()

        return await finalize_crescendo_trace(trace, self._judge, persona.name, rubric_name, start_time)
