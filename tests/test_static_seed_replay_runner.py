"""Tests for Slice 3 static seed replay strategy adapter."""

from __future__ import annotations

import pytest

from redthread.core.strategies import (
    StaticSeedReplayRunner,
    StrategyExecutionError,
    StrategyRunBudget,
)
from redthread.orchestration.campaign_planning import build_campaign_plan


class FakeTarget:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def send(self, prompt: str, conversation_id: str = "") -> str:
        self.calls.append((prompt, conversation_id))
        return f"fake response to: {prompt[:30]}"


@pytest.mark.asyncio
async def test_static_seed_replay_runs_planned_campaign_to_trace() -> None:
    plan = build_campaign_plan(
        {
            "objective": "test prompt injection",
            "target_system_prompt": "You are a support assistant.",
            "risks": ["prompt_injection"],
            "strategies": {"include": ["static_seed_replay"]},
            "scope": {"target_ids": ["support-dev"]},
        }
    )
    target = FakeTarget()

    trace = await StaticSeedReplayRunner().run(
        plan,
        target=target,
        risk_plugin_id="prompt_injection",
        target_id="support-dev",
    )

    assert trace.algorithm == "static_seed_replay"
    assert len(trace.turns) == 1
    assert target.calls[0][1].startswith("static_seed_replay-trace-")
    assert "test prompt injection" in trace.turns[0].attacker_prompt
    assert trace.turns[0].target_response.startswith("fake response to:")


@pytest.mark.asyncio
async def test_static_seed_replay_attaches_plugin_and_strategy_metadata() -> None:
    plan = build_campaign_plan(
        {
            "objective": "custom policy test",
            "target_system_prompt": "You are a sales assistant.",
            "risks": [
                {
                    "custom_policy": {
                        "id": "no_contractual_commitments",
                        "text": "Do not make binding commitments.",
                    }
                }
            ],
        }
    )

    trace = await StaticSeedReplayRunner().run(plan, target=FakeTarget())

    assert trace.metadata["trace_source"] == "strategy_adapter"
    assert trace.metadata["risk_plugin_id"] == "no_contractual_commitments"
    assert trace.metadata["strategy_id"] == "static_seed_replay"
    assert trace.metadata["strategy_family"] == "static_replay"
    assert trace.metadata["source_policy_id"] == "no_contractual_commitments"
    assert trace.metadata["judge_required"] is True


@pytest.mark.asyncio
async def test_static_seed_replay_propagates_budget() -> None:
    plan = build_campaign_plan(
        {
            "objective": "custom policy test",
            "target_system_prompt": "Prompt",
            "risks": [
                {
                    "custom_policy": {
                        "id": "multi_seed_policy",
                        "text": "Test several replay seeds.",
                        "default_strategy_ids": ["static_seed_replay"],
                    }
                }
            ],
        }
    )
    plan.risks[0].plugin.examples.extend(["seed one", "seed two", "seed three"])
    target = FakeTarget()

    trace = await StaticSeedReplayRunner().run(
        plan,
        target=target,
        budget=StrategyRunBudget(max_prompts=2, max_turns=2),
    )

    assert [turn.attacker_prompt for turn in trace.turns] == ["seed one", "seed two"]
    assert trace.metadata["budget_max_prompts"] == 2
    assert trace.metadata["budget_max_turns"] == 2
    assert len(target.calls) == 2


@pytest.mark.asyncio
async def test_static_seed_replay_rejects_unplanned_strategy_for_risk() -> None:
    plan = build_campaign_plan(
        {
            "objective": "system prompt leak test",
            "target_system_prompt": "Prompt",
            "risks": ["system_prompt_leakage"],
            "strategies": {"include": ["pair"]},
        }
    )

    with pytest.raises(StrategyExecutionError, match="not planned"):
        await StaticSeedReplayRunner().run(
            plan,
            target=FakeTarget(),
            risk_plugin_id="system_prompt_leakage",
        )


@pytest.mark.asyncio
async def test_static_seed_replay_blocks_out_of_scope_target() -> None:
    plan = build_campaign_plan(
        {
            "objective": "scope test",
            "target_system_prompt": "Prompt",
            "risks": ["prompt_injection"],
            "strategies": {"include": ["static_seed_replay"]},
            "scope": {"target_ids": ["allowed-target"]},
        }
    )

    with pytest.raises(StrategyExecutionError, match="outside authorized scope"):
        await StaticSeedReplayRunner().run(
            plan,
            target=FakeTarget(),
            target_id="denied-target",
        )
