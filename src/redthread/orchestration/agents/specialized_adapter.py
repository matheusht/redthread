"""Adapter exposing the specialized chain through the campaign result contract."""

from __future__ import annotations

from datetime import datetime, timezone
from time import monotonic
from typing import Any
from uuid import uuid4

from redthread.models import (
    AttackOutcome,
    AttackResult,
    AttackTrace,
    ConversationTurn,
    JudgeVerdict,
)
from redthread.orchestration.agents.agent_chain import run_specialized_pipeline
from redthread.orchestration.agents.models import AgentPhaseState
from redthread.personas.models import Persona


def _conversation_turn(index: int, raw: dict[str, Any]) -> ConversationTurn:
    """Adapt canonical phase turns while reading legacy aliases."""
    prompt = raw.get("attacker_prompt")
    if prompt is None:
        prompt = raw.get("probe") or raw.get("pretext") or raw.get("payload") or ""
    return ConversationTurn(
        turn_number=index,
        attacker_prompt=str(prompt),
        target_response=str(raw.get("response", "")),
        improvement_rationale=str(raw.get("agent", "")),
    )


def _result(
    persona: Persona,
    target_prompt: str,
    rubric: str,
    turns: list[ConversationTurn],
    metadata: dict[str, Any],
    outcome: AttackOutcome,
    started: float,
) -> AttackResult:
    trace = AttackTrace(
        persona=persona,
        algorithm="agent_chain",
        turns=turns,
        outcome=outcome,
        metadata={"target_system_prompt": target_prompt, **metadata},
        ended_at=datetime.now(timezone.utc),
    )
    return AttackResult(
        trace=trace,
        verdict=JudgeVerdict(
            score=0.0,
            raw_score=0,
            reasoning="Specialized chain requires JudgeAgent confirmation.",
            feedback="",
            rubric_name=rubric,
            is_jailbreak=False,
        ),
        iterations_used=len(turns),
        duration_seconds=monotonic() - started,
    )


async def run_specialized_attack(state: AgentPhaseState) -> AttackResult:
    """Run Recon -> Social -> Exploit and adapt its trace for supervision."""
    started = monotonic()
    persona = Persona.model_validate(state.get("persona_dict", {}))
    metadata = state.get("metadata", {})
    settings = metadata.get("settings_dict", {})
    target_prompt = state.get("target_system_prompt", "")
    rubric = metadata.get("rubric_name", "authorization_bypass")
    if settings.get("dry_run"):
        return _result(
            persona, target_prompt, rubric, [], {"dry_run": True}, AttackOutcome.SKIPPED, started
        )
    try:
        trace_id = metadata.get("trace_id", f"agent-chain-{uuid4().hex[:8]}")
        state = {
            **state,
            "metadata": {
                **metadata,
                "trace_id": trace_id,
                "target_conversation_id": f"{trace_id}:target",
            },
        }
        final_state = await run_specialized_pipeline(state)
        turns = [
            _conversation_turn(index, raw)
            for index, raw in enumerate(final_state.get("turns", []), 1)
        ]
        return _result(
            persona,
            target_prompt,
            rubric,
            turns,
            {
                "specialized_is_jailbreak": bool(final_state.get("is_jailbreak")),
                "phase_errors": list(final_state.get("phase_errors") or []),
            },
            AttackOutcome.ERROR if final_state.get("phase_errors") else AttackOutcome.FAILURE,
            started,
        )
    except Exception as exc:
        return _result(
            persona,
            target_prompt,
            rubric,
            [],
            {"specialized_error": str(exc)},
            AttackOutcome.ERROR,
            started,
        )


class SpecializedAttackRunner:
    """Registry-compatible runner for direct algorithm callers."""

    def __init__(self, settings: Any) -> None:
        self.settings = settings

    async def run(
        self,
        persona: Persona,
        target_system_prompt: str = "",
        rubric_name: str = "authorization_bypass",
    ) -> AttackResult:
        return await run_specialized_attack({
            "persona_dict": persona.model_dump(mode="json"),
            "target_system_prompt": target_system_prompt,
            "metadata": {
                "settings_dict": self.settings.model_dump(mode="json"),
                "rubric_name": rubric_name,
            },
        })


__all__ = ["SpecializedAttackRunner", "run_specialized_attack"]
