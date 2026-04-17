from __future__ import annotations

import pytest

from redthread.config.settings import RedThreadSettings
from redthread.tools.authorization.tool_context import AUTHORIZATION_ACTION_METADATA_KEY
from redthread.tools.base import ToolContext
from redthread.tools.sandbox_tool import SandboxInput, SandboxTool


class DummyTarget:
    def __init__(self) -> None:
        self.calls = 0

    async def send(self, prompt: str, conversation_id: str = "") -> str:
        self.calls += 1
        return f"echo:{prompt}:{conversation_id}"


class DummyJudge:
    def __init__(self, settings: RedThreadSettings) -> None:
        self.settings = settings

    def evaluate_turn(self, replay_turn: object, rubric_name: str = "") -> float:
        return 1.0


@pytest.mark.asyncio
async def test_sandbox_tool_preserves_plain_send_without_auth_metadata(monkeypatch: object) -> None:
    target = DummyTarget()
    monkeypatch.setattr("redthread.pyrit_adapters.targets.build_target", lambda settings: target)
    monkeypatch.setattr("redthread.evaluation.judge.JudgeAgent", DummyJudge)
    tool = SandboxTool()
    ctx = ToolContext(settings=RedThreadSettings(), campaign_id="camp-1")

    result = await tool.call(
        SandboxInput(attack_payload="payload", guardrail_clause="block it", trace_id="trace-1"),
        ctx,
    )

    assert result.success is True
    assert result.data["replay_response"].endswith(":sandbox-trace-1")
    assert result.metadata["conversation_id"] == "sandbox-trace-1"
    assert target.calls == 1


@pytest.mark.asyncio
async def test_sandbox_tool_blocks_denied_action_before_target_send(monkeypatch: object) -> None:
    target = DummyTarget()
    monkeypatch.setattr("redthread.pyrit_adapters.targets.build_target", lambda settings: target)
    monkeypatch.setattr("redthread.evaluation.judge.JudgeAgent", DummyJudge)
    tool = SandboxTool()
    ctx = ToolContext(
        settings=RedThreadSettings(),
        campaign_id="camp-1",
        metadata={
            AUTHORIZATION_ACTION_METADATA_KEY: {
                "actor_id": "exec-1",
                "actor_role": "executor",
                "capability": "memory.write",
                "tool_name": "memory.write",
                "target_sensitivity": "medium",
                "provenance": {
                    "source_kind": "external_tool",
                    "trust_level": "derived",
                    "origin_id": "tool-1",
                },
                "requested_effect": "write",
            }
        },
    )

    result = await tool.call(
        SandboxInput(attack_payload="payload", guardrail_clause="block it", trace_id="trace-1"),
        ctx,
    )

    assert result.success is False
    assert result.error == "Authorization blocked sandbox tool: deny"
    assert result.metadata["authorization_decision"]["decision"] == "deny"
    assert target.calls == 0


@pytest.mark.asyncio
async def test_sandbox_tool_allows_safe_action_and_records_decision(monkeypatch: object) -> None:
    target = DummyTarget()
    monkeypatch.setattr("redthread.pyrit_adapters.targets.build_target", lambda settings: target)
    monkeypatch.setattr("redthread.evaluation.judge.JudgeAgent", DummyJudge)
    tool = SandboxTool()
    ctx = ToolContext(
        settings=RedThreadSettings(),
        campaign_id="camp-1",
        metadata={
            AUTHORIZATION_ACTION_METADATA_KEY: {
                "actor_id": "retriever-1",
                "actor_role": "retriever",
                "capability": "tool.read",
                "tool_name": "tool.read",
                "target_sensitivity": "low",
                "provenance": {
                    "source_kind": "internal_agent",
                    "trust_level": "trusted",
                    "origin_id": "retriever-1",
                },
                "requested_effect": "read",
            }
        },
    )

    result = await tool.call(
        SandboxInput(attack_payload="payload", guardrail_clause="block it", trace_id="trace-1"),
        ctx,
    )

    assert result.success is True
    assert result.metadata["authorization_decision"]["decision"] == "allow"
    assert result.metadata["conversation_id"] == "sandbox-trace-1"
    assert target.calls == 1
