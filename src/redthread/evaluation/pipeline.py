"""DeepEval-style evaluation coordinator for the golden dataset."""

from __future__ import annotations

import logging

from redthread.config.settings import RedThreadSettings
from redthread.evaluation.heuristics import score_trace_heuristically
from redthread.evaluation.metrics import compute_metrics
from redthread.evaluation.results import EvaluationMetrics, TraceEvalResult
from redthread.models import ConversationTurn

logger = logging.getLogger(__name__)


class EvaluationPipeline:
    """Run golden traces through a live judge or sealed fallback path."""

    def __init__(self, settings: RedThreadSettings) -> None:
        self.settings = settings

    def _score_trace_heuristically(self, attacker_prompt: str, target_response: str) -> float:
        """Compatibility wrapper for the extracted deterministic scorer."""
        return score_trace_heuristically(attacker_prompt, target_response)

    def _evaluate_trace_fallback(
        self,
        trace_id: str,
        category: str,
        attacker_prompt: str,
        target_response: str,
        expected_min: float,
        expected_max: float,
        error: Exception,
    ) -> TraceEvalResult:
        """Return degraded evidence when live judge execution fails."""
        score = self._score_trace_heuristically(attacker_prompt, target_response)
        reason = str(error)
        logger.warning(
            "DEGRADED EVIDENCE: golden trace %s used heuristic fallback after live judge failure: %s",
            trace_id,
            reason,
        )
        return TraceEvalResult(
            trace_id=trace_id,
            category=category,
            expected_min=expected_min,
            expected_max=expected_max,
            actual_score=score,
            within_range=expected_min <= score <= expected_max,
            evidence_mode="live_judge_fallback",
            evidence_label="Live judge failed; deterministic heuristic fallback used.",
            error=reason,
            fallback_reason=reason,
            evidence_class="fallback_heuristic",
        )

    async def evaluate_trace(
        self,
        trace_id: str,
        category: str,
        objective: str,
        system_prompt: str,
        attacker_prompt: str,
        target_response: str,
        expected_min: float,
        expected_max: float,
        tactic: str,
    ) -> TraceEvalResult:
        """Evaluate one golden trace against JudgeAgent."""
        if self.settings.dry_run:
            score = self._score_trace_heuristically(attacker_prompt, target_response)
            return TraceEvalResult(
                trace_id=trace_id,
                category=category,
                expected_min=expected_min,
                expected_max=expected_max,
                actual_score=score,
                within_range=expected_min <= score <= expected_max,
                evidence_mode="sealed_heuristic",
                evidence_label="Sealed dry-run heuristic evaluation.",
                evidence_class="sealed_heuristic",
            )

        try:
            from redthread.evaluation.judge import JudgeAgent
            from redthread.models import AttackOutcome, AttackTrace
            from redthread.personas.models import MitreAtlasTactic, Persona

            judge = JudgeAgent(self.settings)
            atlas_tactic = MitreAtlasTactic.INITIAL_ACCESS
            for member in MitreAtlasTactic:
                if member.value.lower() in tactic.lower() or tactic.lower() in member.name.lower():
                    atlas_tactic = member
                    break

            persona = Persona(
                name=f"golden-{trace_id}",
                tactic=atlas_tactic,
                technique="AML.T0054 — LLM Prompt Injection",
                cover_story="Golden dataset evaluation",
                hidden_objective=objective,
                system_prompt="",
                psychological_triggers=[],
            )
            trace = AttackTrace(
                id=f"golden-{trace_id}",
                persona=persona,
                algorithm="golden_dataset",
                turns=[ConversationTurn(
                    turn_number=1,
                    attacker_prompt=attacker_prompt,
                    target_response=target_response,
                )],
                outcome=AttackOutcome.SUCCESS if expected_min >= 4.0 else AttackOutcome.FAILURE,
                metadata={"target_system_prompt": system_prompt},
            )
            verdict = await judge.evaluate(trace, rubric_name="authorization_bypass")
            return TraceEvalResult(
                trace_id=trace_id,
                category=category,
                expected_min=expected_min,
                expected_max=expected_max,
                actual_score=verdict.score,
                within_range=expected_min <= verdict.score <= expected_max,
                evidence_mode="live_judge",
                evidence_label="Live judge evaluation completed successfully.",
                verdict=verdict,
                evidence_class="live_judge",
            )
        except Exception as exc:
            return self._evaluate_trace_fallback(
                trace_id=trace_id,
                category=category,
                attacker_prompt=attacker_prompt,
                target_response=target_response,
                expected_min=expected_min,
                expected_max=expected_max,
                error=exc,
            )

    def compute_metrics(self, results: list[TraceEvalResult]) -> EvaluationMetrics:
        """Compatibility wrapper for extracted aggregate metrics."""
        return compute_metrics(results)
