from __future__ import annotations

from dataclasses import dataclass

import pytest

from redthread.pyrit_adapters.client import RedThreadTarget
from redthread.pyrit_adapters.execution_records import ExecutionMetadata


@dataclass
class FakeMessagePiece:
    role: str = "assistant"
    original_value: str = ""
    conversation_id: str = ""
    converted_value: str | None = None


@dataclass
class FakeMessage:
    message_pieces: list[FakeMessagePiece]


class SuccessfulPyritTarget:
    def __init__(self) -> None:
        self.seen_message: FakeMessage | None = None

    async def send_prompt_async(self, message: FakeMessage) -> list[FakeMessage]:
        self.seen_message = message
        return [FakeMessage([FakeMessagePiece(original_value="ok", converted_value="ok")])]


class FailingPyritTarget:
    async def send_prompt_async(self, message: FakeMessage) -> list[FakeMessage]:
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_send_records_successful_live_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "redthread.pyrit_adapters.client.import_pyrit_runtime",
        lambda: (FakeMessage, FakeMessagePiece, object),
    )
    records = []
    target = RedThreadTarget(
        pyrit_target=SuccessfulPyritTarget(),
        model_name="gpt-4o",
        execution_recorder=records.append,
    )

    response = await target.send(
        prompt="hello",
        execution_metadata=ExecutionMetadata(
            seam="judge.score",
            role="judge",
            evidence_class="live_judge",
            conversation_id="conv-1",
        ),
    )

    assert response == "ok"
    assert len(records) == 1
    assert records[0].seam == "judge.score"
    assert records[0].conversation_id == "conv-1"
    assert records[0].model_name == "gpt-4o"
    assert records[0].success is True
    assert records[0].error is None


@pytest.mark.asyncio
async def test_send_records_failed_live_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "redthread.pyrit_adapters.client.import_pyrit_runtime",
        lambda: (FakeMessage, FakeMessagePiece, object),
    )
    records = []
    target = RedThreadTarget(
        pyrit_target=FailingPyritTarget(),
        model_name="gpt-4o",
        execution_recorder=records.append,
    )

    with pytest.raises(RuntimeError, match="boom"):
        await target.send(
            prompt="hello",
            execution_metadata=ExecutionMetadata(
                seam="judge.autocot",
                role="judge",
                evidence_class="live_judge",
                conversation_id="conv-2",
            ),
        )

    assert len(records) == 1
    assert records[0].seam == "judge.autocot"
    assert records[0].conversation_id == "conv-2"
    assert records[0].success is False
    assert records[0].error == "RuntimeError: boom"
