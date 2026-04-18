from __future__ import annotations

from dataclasses import dataclass

import pytest

from redthread.orchestration.execution_truth_summary import build_execution_truth_summary
from redthread.pyrit_adapters.client import RedThreadTarget
from redthread.pyrit_adapters.execution_context import capture_execution_records
from redthread.pyrit_adapters.execution_records import ExecutionMetadata, ExecutionRecord


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
    async def send_prompt_async(self, message: FakeMessage) -> list[FakeMessage]:
        return [FakeMessage([FakeMessagePiece(original_value="ok")])]


def test_execution_truth_summary_aggregates_counts() -> None:
    summary = build_execution_truth_summary(
        [
            ExecutionRecord(
                seam="judge.score",
                role="judge",
                evidence_class="live_judge",
                model_name="gpt-4o",
                conversation_id="1",
                runtime_mode="live_provider",
                success=True,
            ),
            ExecutionRecord(
                seam="telemetry.canary",
                role="telemetry",
                evidence_class="telemetry_signal",
                model_name="gpt-4o-mini",
                conversation_id="2",
                runtime_mode="live_provider",
                success=False,
                error="timeout",
            ),
        ]
    )

    assert summary["execution_record_total"] == 2
    assert summary["failed_execution_count"] == 1
    assert summary["seam_counts"] == {"judge.score": 1, "telemetry.canary": 1}
    assert summary["evidence_class_counts"] == {"live_judge": 1, "telemetry_signal": 1}


@pytest.mark.asyncio
async def test_execution_context_captures_target_records(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "redthread.pyrit_adapters.client.import_pyrit_runtime",
        lambda: (FakeMessage, FakeMessagePiece, object),
    )
    records = []
    target = RedThreadTarget(pyrit_target=SuccessfulPyritTarget(), model_name="gpt-4o")

    with capture_execution_records(records):
        await target.send(
            prompt="hello",
            execution_metadata=ExecutionMetadata(
                seam="judge.score",
                role="judge",
                evidence_class="live_judge",
                conversation_id="ctx-1",
            ),
        )

    assert len(records) == 1
    assert records[0].conversation_id == "ctx-1"
    assert records[0].seam == "judge.score"
