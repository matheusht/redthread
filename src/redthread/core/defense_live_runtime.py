from __future__ import annotations

from redthread.config.settings import RedThreadSettings
from redthread.core.defense_assets import (
    DEFENSE_ARCHITECT_SYSTEM_PROMPT,
    DEFENSE_ARCHITECT_USER_TEMPLATE,
)
from redthread.core.defense_evidence import LIVE_VALIDATION_ERROR
from redthread.core.defense_models import GuardrailProposal, IsolatedSegment, ValidationResult
from redthread.core.defense_replay_runner import DefenseReplayRunner
from redthread.models import AttackTrace, JudgeVerdict
from redthread.pyrit_adapters.targets import (
    ExecutionMetadata,
    ExecutionRecorder,
    send_with_execution_metadata,
)


async def generate_live_guardrail(
    settings: RedThreadSettings,
    *,
    segment: IsolatedSegment,
    verdict: JudgeVerdict,
    execution_recorder: ExecutionRecorder | None = None,
) -> str:
    from redthread.pyrit_adapters import targets as target_builders

    architect_llm = target_builders.build_defense_architect(
        settings,
        execution_recorder=execution_recorder,
    )
    user_msg = DEFENSE_ARCHITECT_USER_TEMPLATE.format(
        tactic=segment.persona_tactic,
        payload=segment.attack_payload,
        response=segment.target_response,
        score=segment.score,
        reasoning=verdict.reasoning,
    )
    try:
        return await send_with_execution_metadata(
            architect_llm,
            prompt=f"[SYSTEM]: {DEFENSE_ARCHITECT_SYSTEM_PROMPT}\n\n[USER]: {user_msg}",
            conversation_id=f"defense-architect-{segment.trace_id}",
            execution_metadata=ExecutionMetadata(
                seam="defense.architect",
                role="defense_architect",
                evidence_class="live_generation",
                metadata={"trace_id": segment.trace_id},
            ),
        )
    finally:
        architect_llm.close()


async def run_live_defense_validation(
    settings: RedThreadSettings,
    *,
    segment: IsolatedSegment,
    proposal: GuardrailProposal,
    trace: AttackTrace,
    execution_recorder: ExecutionRecorder | None = None,
) -> ValidationResult:
    runner = DefenseReplayRunner(settings.success_threshold)
    patched_target = None
    try:
        from redthread.evaluation.judge import JudgeAgent
        from redthread.pyrit_adapters import targets as target_builders

        patched_target = target_builders.build_target(
            settings,
            execution_recorder=execution_recorder,
        )
        judge = JudgeAgent(settings, execution_recorder=execution_recorder)
        return await runner.run_live(
            target=patched_target,
            judge=judge,
            attack_payload=segment.attack_payload,
            guardrail_clause=proposal.clause,
            trace_id=trace.id,
        )
    except Exception as exc:
        return ValidationResult(
            passed=False,
            replay_response="",
            judge_score=settings.success_threshold,
            exploit_replay_passed=False,
            benign_passed=False,
            replay_suite_id="default-defense-replay-v4",
            validation_mode="live",
            evidence_mode=LIVE_VALIDATION_ERROR,
            failure_reason=f"defense validation failed: {exc}",
        )
    finally:
        if patched_target is not None:
            patched_target.close()
