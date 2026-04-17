"""Authorization helpers for live defense replay validation."""

from __future__ import annotations

from redthread.core.defense_models import ReplayCaseResult
from redthread.orchestration.models import ActionEffect, ActionEnvelope, AuthorizationDecision
from redthread.tools.authorization import authorize_live_action


def authorize_replay_case(
    *,
    trace_id: str,
    case_id: str,
    kind: str,
    prompt: str,
    policies: list | None = None,
) -> AuthorizationDecision:
    action = ActionEnvelope(
        actor_id=f"defense-validator-{trace_id}",
        actor_role="defense_validator",
        capability="target.replay",
        tool_name="target.replay",
        arguments={
            "trace_id": trace_id,
            "case_id": case_id,
            "kind": kind,
            "prompt_excerpt": prompt[:120],
        },
        target_sensitivity="low",
        provenance={
            "source_kind": "internal_agent",
            "trust_level": "trusted",
            "origin_id": f"defense-validator-{trace_id}",
            "parent_ids": [trace_id],
        },
        requested_effect=ActionEffect.EXECUTE,
    )
    return authorize_live_action(action, policies=policies)


def build_blocked_replay_case(
    *,
    case_id: str,
    kind: str,
    prompt: str,
    decision: AuthorizationDecision,
    rubric_name: str = "authorization_bypass",
) -> ReplayCaseResult:
    return ReplayCaseResult(
        case_id=case_id,
        kind=kind,
        prompt=prompt,
        response="",
        passed=False,
        rubric_name=rubric_name,
        failure_reason=f"authorization blocked replay: {decision.decision.value}",
        blocked_by_authorization=True,
        authorization_decision=decision.model_dump(mode="json"),
    )
