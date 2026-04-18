"""JudgeAgent — G-Eval methodology with Prometheus 2 evaluation protocol."""

from __future__ import annotations

import logging
from typing import Any

import yaml

from redthread.config.settings import RedThreadSettings
from redthread.evaluation.judge_support import (
    AUTO_COT_PROMPT,
    RUBRICS_DIR,
    SCORING_PROMPT,
    evaluate_turn_heuristic,
    format_conversation,
    format_scale,
    parse_verdict,
)
from redthread.models import AttackTrace, ConversationTurn, JudgeVerdict
from redthread.observability.tracing import traced
from redthread.pyrit_adapters.targets import ExecutionMetadata, ExecutionRecorder

logger = logging.getLogger(__name__)


class JudgeAgent:
    """G-Eval methodology judge using the heavyweight model (GPT-4o)."""

    def __init__(
        self,
        settings: RedThreadSettings,
        execution_recorder: ExecutionRecorder | None = None,
    ) -> None:
        self.settings = settings
        self._execution_recorder = execution_recorder
        self._judge_llm = None
        self._rubric_cache: dict[str, dict[str, Any]] = {}

    def _get_judge_llm(self) -> Any:
        if self._judge_llm is None:
            from redthread.pyrit_adapters.targets import build_judge_llm

            self._judge_llm = build_judge_llm(
                self.settings,
                execution_recorder=self._execution_recorder,
            )
        return self._judge_llm

    def load_rubric(self, rubric_name: str) -> dict[str, Any]:
        if rubric_name in self._rubric_cache:
            return self._rubric_cache[rubric_name]

        rubric_path = RUBRICS_DIR / f"{rubric_name}.yaml"
        if not rubric_path.exists():
            raise FileNotFoundError(
                f"Rubric '{rubric_name}' not found at {rubric_path}. "
                f"Available: {[p.stem for p in RUBRICS_DIR.glob('*.yaml')]}"
            )
        with rubric_path.open() as handle:
            rubric = yaml.safe_load(handle)
        self._rubric_cache[rubric_name] = rubric
        return rubric

    @traced
    async def _generate_evaluation_steps(
        self, rubric: dict[str, Any], rubric_name: str
    ) -> str:
        prompt = AUTO_COT_PROMPT.format(
            rubric_name=rubric_name,
            rubric_description=rubric.get("description", ""),
            scale_text=format_scale(rubric),
        )
        steps = await self._get_judge_llm().send(
            prompt=prompt,
            conversation_id=f"judge-cot-{rubric_name}",
            execution_metadata=ExecutionMetadata(
                seam="judge.autocot",
                role="judge",
                evidence_class="live_judge",
            ),
        )
        logger.debug("Auto-CoT evaluation steps generated:\n%s", steps)
        return steps

    @traced
    async def evaluate(
        self,
        trace: AttackTrace,
        rubric_name: str = "authorization_bypass",
    ) -> JudgeVerdict:
        rubric = self.load_rubric(rubric_name)
        evaluation_steps = await self._generate_evaluation_steps(rubric, rubric_name)
        raw_verdict = await self._get_judge_llm().send(
            prompt=SCORING_PROMPT.format(
                evaluation_steps=evaluation_steps,
                scale_text=format_scale(rubric),
                conversation_text=format_conversation(trace),
            ),
            conversation_id=f"judge-score-{trace.id}",
            execution_metadata=ExecutionMetadata(
                seam="judge.score",
                role="judge",
                evidence_class="live_judge",
            ),
        )
        return self._parse_verdict(
            raw=raw_verdict,
            rubric_name=rubric_name,
            success_threshold=self.settings.success_threshold,
        )

    def evaluate_turn(
        self,
        turn: ConversationTurn,
        rubric_name: str = "authorization_bypass",
    ) -> float:
        return evaluate_turn_heuristic(turn)

    def evaluate_turn_raw(
        self,
        attacker_prompt: str,
        target_response: str,
        rubric_name: str = "authorization_bypass",
    ) -> float:
        return self.evaluate_turn(
            ConversationTurn(
                turn_number=0,
                attacker_prompt=attacker_prompt,
                target_response=target_response,
            ),
            rubric_name,
        )

    def _parse_verdict(
        self,
        raw: str,
        rubric_name: str,
        success_threshold: float,
    ) -> JudgeVerdict:
        return parse_verdict(raw, rubric_name, success_threshold)
