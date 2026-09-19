from __future__ import annotations

import pytest

from redthread.orchestration.models import ActionEnvelope
from redthread.pyrit_adapters.controlled import (
    ControlledLiveAdapter,
    LiveAdapterGate,
    LiveAuthorizationInterceptionError,
)


class DummyTarget:
    def __init__(self) -> None:
        self.calls = 0

    async def send(self, prompt: str, conversation_id: str = "") -> str:
        self.calls += 1
        return f"echo:{prompt}"


@pytest.mark.asyncio
async def test_controlled_live_adapter_fails_closed_without_approval() -> None:
    adapter = ControlledLiveAdapter(DummyTarget(), LiveAdapterGate())

    with pytest.raises(RuntimeError, match="locked"):
        await adapter.send("hello")


@pytest.mark.asyncio
async def test_controlled_live_adapter_allows_after_approval() -> None:
    target = DummyTarget()
    adapter = ControlledLiveAdapter(
        target,
        LiveAdapterGate(enabled=True, approval_id="APR-001", replay_bundle_id="phase-8e-smoke"),
    )

    response = await adapter.send("hello")

    assert response == "echo:hello"
    assert target.calls == 1


@pytest.mark.asyncio
async def test_controlled_live_adapter_blocks_denied_action_before_send() -> None:
    target = DummyTarget()
    adapter = ControlledLiveAdapter(
        target,
        LiveAdapterGate(enabled=True, approval_id="APR-001", replay_bundle_id="phase-8e-smoke"),
    )
    action = ActionEnvelope(
        actor_id="exec-1",
        actor_role="executor",
        capability="memory.write",
        tool_name="memory.write",
        target_sensitivity="medium",
        provenance={
            "source_kind": "external_tool",
            "trust_level": "derived",
            "origin_id": "tool-1",
        },
        requested_effect="write",
    )

    with pytest.raises(LiveAuthorizationInterceptionError, match="blocked action: deny") as exc_info:
        await adapter.send("write this", action=action)

    assert exc_info.value.decision.decision.value == "deny"
    assert target.calls == 0


@pytest.mark.asyncio
async def test_controlled_live_adapter_allows_safe_action_after_intercept() -> None:
    target = DummyTarget()
    adapter = ControlledLiveAdapter(
        target,
        LiveAdapterGate(enabled=True, approval_id="APR-001", replay_bundle_id="phase-8e-smoke"),
    )
    action = ActionEnvelope(
        actor_id="retriever-1",
        actor_role="retriever",
        capability="tool.read",
        tool_name="tool.read",
        target_sensitivity="low",
        provenance={
            "source_kind": "internal_agent",
            "trust_level": "trusted",
            "origin_id": "retriever-1",
        },
        requested_effect="read",
    )

    response = await adapter.send("safe read", action=action)

    assert response == "echo:safe read"
    assert target.calls == 1
