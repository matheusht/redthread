"""Unit tests for client retry and canary containment preservation (Issues #95, #96)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from redthread.orchestration.models import ActionEnvelope
from redthread.pyrit_adapters.client import RedThreadTarget
from redthread.pyrit_adapters.client_retry import is_retryable_error, send_with_retry
from redthread.pyrit_adapters.controlled import (
    ControlledLiveAdapter,
    LiveAdapterGate,
    LiveAuthorizationInterceptionError,
)
from redthread.pyrit_adapters.execution_context import capture_execution_records
from redthread.pyrit_adapters.execution_records import ExecutionMetadata
from redthread.pyrit_adapters.send_helpers import send_with_execution_metadata


class DummyRateLimitError(Exception):
    status = 429


class DummyFatalError(Exception):
    status = 400


def test_is_retryable_error() -> None:
    assert is_retryable_error(DummyRateLimitError("Rate limit exceeded"))
    assert is_retryable_error(ConnectionError("Connection reset by peer"))
    assert is_retryable_error(TimeoutError("Request timed out"))
    assert not is_retryable_error(DummyFatalError("Bad Request"))
    assert not is_retryable_error(ValueError("Invalid argument"))


@pytest.mark.asyncio
async def test_send_with_retry_succeeds_after_transient() -> None:
    attempts = 0

    async def flaky_call() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise DummyRateLimitError("Too Many Requests")
        return "success"

    res = await send_with_retry(flaky_call, max_retries=3, initial_delay=0.01)
    assert res == "success"
    assert attempts == 3


@pytest.mark.asyncio
async def test_send_with_retry_fails_fast_on_fatal() -> None:
    attempts = 0

    async def fatal_call() -> None:
        nonlocal attempts
        attempts += 1
        raise DummyFatalError("Bad Request")

    with pytest.raises(DummyFatalError):
        await send_with_retry(fatal_call, max_retries=3, initial_delay=0.01)
    assert attempts == 1


@pytest.mark.asyncio
async def test_controlled_adapter_records_execution_on_block() -> None:
    target = MagicMock(spec=RedThreadTarget)
    target._record_execution = MagicMock()
    gate = LiveAdapterGate(enabled=True, approval_id="app-1", replay_bundle_id="rep-1")
    adapter = ControlledLiveAdapter(target=target, gate=gate)

    action = ActionEnvelope(
        action_id="act-1",
        actor_id="exec-1",
        actor_role="executor",
        capability="shell.exec",
        tool_name="shell_exec",
        target_sensitivity="high",
        provenance={
            "source_kind": "external_tool",
            "trust_level": "untrusted",
            "origin_id": "tool-1",
        },
        requested_effect="execute",
        arguments={"cmd": "rm -rf /"},
        canary_tags=["canary-123"],
    )

    with pytest.raises(LiveAuthorizationInterceptionError):
        await adapter.send("test", action=action)

    assert target._record_execution.called
    kwargs = target._record_execution.call_args.kwargs
    assert kwargs["success"] is False
    assert kwargs["execution_metadata"].canary_tags == ["canary-123"]


@pytest.mark.asyncio
async def test_send_with_execution_metadata_fallback_records_audit() -> None:
    recorded = []

    class TargetWithoutMetadata:
        model_name = "test-model"

        async def send(self, prompt: str, conversation_id: str = "") -> str:
            return "response"

    target = TargetWithoutMetadata()
    metadata = ExecutionMetadata(
        seam="test",
        role="test",
        evidence_class="test",
        canary_tags=["tag-abc"],
    )

    with capture_execution_records(recorded):
        res = await send_with_execution_metadata(
            target,
            prompt="hello",
            conversation_id="c-1",
            execution_metadata=metadata,
        )

    assert res == "response"
    assert len(recorded) == 1
    assert recorded[0].metadata["canary_tags"] == ["tag-abc"]
    assert recorded[0].metadata.get("signature_fallback") is True
