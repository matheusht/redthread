from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

from redthread.config.settings import RedThreadSettings, TargetBackend
from redthread.daemon.monitor import SecurityGuardDaemon
from redthread.pyrit_adapters.client import RedThreadTarget
from redthread.telemetry.collector import TelemetryCollector


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
    def __init__(self, response: str) -> None:
        self._response = response

    async def send_prompt_async(self, message: FakeMessage) -> list[FakeMessage]:
        return [FakeMessage([FakeMessagePiece(original_value=self._response)])]


def make_settings(tmp_path: Path) -> RedThreadSettings:
    return RedThreadSettings(
        target_backend=TargetBackend.OPENAI,
        target_model="gpt-4o-mini",
        openai_api_key="test-key",
        telemetry_enabled=True,
        log_dir=tmp_path / "logs",
        memory_dir=tmp_path / "memory",
    )


@pytest.mark.asyncio
async def test_canary_batch_emits_execution_record(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "redthread.pyrit_adapters.client.import_pyrit_runtime",
        lambda: (FakeMessage, FakeMessagePiece, object),
    )
    monkeypatch.setattr("redthread.telemetry.collector.CANARY_PROMPTS", {"c1": "ping"})
    collector = TelemetryCollector(make_settings(tmp_path))
    collector.record_interaction = _stub_record_interaction  # type: ignore[method-assign]
    records = []
    target = RedThreadTarget(
        pyrit_target=SuccessfulPyritTarget("pong"),
        model_name="gpt-4o-mini",
        execution_recorder=records.append,
    )

    await collector.inject_canary_batch(target)

    assert len(records) == 1
    assert records[0].seam == "telemetry.canary"
    assert records[0].role == "telemetry"
    assert records[0].evidence_class == "telemetry_signal"
    assert records[0].metadata["canary_id"] == "c1"


@pytest.mark.asyncio
async def test_daemon_warmup_emits_execution_record(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "redthread.pyrit_adapters.client.import_pyrit_runtime",
        lambda: (FakeMessage, FakeMessagePiece, object),
    )
    monkeypatch.setattr("redthread.daemon.monitor.asyncio.sleep", _noop_sleep)
    monkeypatch.setattr("redthread.telemetry.prompts.CANARY_PROMPTS", {"w1": "warmup"})
    records = []
    daemon = SecurityGuardDaemon(make_settings(tmp_path), execution_recorder=records.append)
    daemon.collector.storage.load_baseline = lambda: []
    daemon.collector.storage.save_baseline = lambda baseline: None
    daemon.collector.record_interaction = _stub_record_interaction  # type: ignore[method-assign]
    target = RedThreadTarget(
        pyrit_target=SuccessfulPyritTarget("warm"),
        model_name="gpt-4o-mini",
        execution_recorder=records.append,
    )

    await daemon._warmup(target)

    assert len(records) == 10
    assert all(record.seam == "telemetry.warmup" for record in records)
    assert all(record.evidence_class == "telemetry_signal" for record in records)


async def _stub_record_interaction(**kwargs):  # type: ignore[no-untyped-def]
    return SimpleNamespace(response_embedding=[0.1])


async def _noop_sleep(delay: float) -> None:
    return None
