"""Tests for deferred live benchmark replay gate plan."""

from __future__ import annotations

from redthread.benchmarks.live_replay_gate import (
    LIVE_REPLAY_ACKNOWLEDGEMENT,
    LIVE_REPLAY_DEFERRED_MESSAGE,
    build_live_replay_gate_plan,
)


def test_live_replay_gate_plan_is_non_executing_and_prompt_safe() -> None:
    plan = build_live_replay_gate_plan(
        target_id="prod-model",
        allowed_target_ids=["prod-model"],
    )

    payload = plan.model_dump()
    assert payload["status"] == "deferred"
    assert payload["target_id"] == "prod-model"
    assert payload["required_manifest_allowlist"] == ["prod-model"]
    assert payload["required_acknowledgement"] == LIVE_REPLAY_ACKNOWLEDGEMENT
    assert payload["legacy_flag_sufficient"] is False
    assert plan.is_acknowledged is False
    assert "raw prompt bodies stay" in payload["raw_prompt_policy"]
    assert "no live provider calls" in payload["execution_policy"]


def test_live_replay_deferred_message_names_future_gates() -> None:
    assert "deferred" in LIVE_REPLAY_DEFERRED_MESSAGE
    assert "manifest allowlist" in LIVE_REPLAY_DEFERRED_MESSAGE
    assert "typed acknowledgement" in LIVE_REPLAY_DEFERRED_MESSAGE
