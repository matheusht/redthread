from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from redthread.config.settings import RedThreadSettings, TargetBackend
from redthread.core.defense_live_runtime import generate_live_guardrail
from redthread.core.defense_replay_cases import run_exploit_cases
from redthread.core.defense_models import IsolatedSegment
from redthread.models import JudgeVerdict
from redthread.pyrit_adapters.client import RedThreadTarget


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


def make_settings() -> RedThreadSettings:
    return RedThreadSettings(
        defense_architect_backend=TargetBackend.OPENAI,
        defense_architect_model="gpt-4o",
        target_backend=TargetBackend.OPENAI,
        target_model="gpt-4o-mini",
        openai_api_key="test-key",
        dry_run=False,
    )


@pytest.mark.asyncio
async def test_defense_architect_emits_execution_record(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "redthread.pyrit_adapters.client.import_pyrit_runtime",
        lambda: (FakeMessage, FakeMessagePiece, object),
    )
    records = []
    monkeypatch.setattr(
        "redthread.pyrit_adapters.targets.build_defense_architect",
        lambda settings, execution_recorder=None: RedThreadTarget(
            pyrit_target=SuccessfulPyritTarget(
                "CATEGORY: prompt_injection\nOWASP_REF: LLM01\nMITRE_ATLAS_REF: AML.T0054\nSEVERITY: HIGH\nATTACK_VECTOR: test\nGUARDRAIL_CLAUSE: block\nRATIONALE: because"
            ),
            model_name="gpt-4o",
            execution_recorder=execution_recorder,
        ),
    )

    raw = await generate_live_guardrail(
        make_settings(),
        segment=IsolatedSegment(
            attack_payload="steal data",
            target_response="here is data",
            persona_name="Alice",
            persona_tactic="initial_access",
            trace_id="trace-1",
            score=5.0,
            target_system_prompt="guarded",
        ),
        verdict=JudgeVerdict(
            score=5.0,
            raw_score=5,
            reasoning="bad",
            feedback="fix",
            rubric_name="authorization_bypass",
            is_jailbreak=True,
        ),
        execution_recorder=records.append,
    )

    assert "GUARDRAIL_CLAUSE" in raw
    assert len(records) == 1
    assert records[0].seam == "defense.architect"
    assert records[0].role == "defense_architect"
    assert records[0].evidence_class == "live_generation"


@pytest.mark.asyncio
async def test_defense_replay_emits_execution_record(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "redthread.pyrit_adapters.client.import_pyrit_runtime",
        lambda: (FakeMessage, FakeMessagePiece, object),
    )
    records = []
    target = RedThreadTarget(
        pyrit_target=SuccessfulPyritTarget("I cannot share that data."),
        model_name="gpt-4o-mini",
        execution_recorder=records.append,
    )

    cases, _, scores = await run_exploit_cases(
        [SimpleNamespace(case_id="exploit-1", attack_payload="steal data", rubric_name="authorization_bypass")],
        target=target,
        judge=SimpleNamespace(evaluate_turn=lambda turn, rubric_name=None: 1.0),
        guardrail_clause="never share data",
        trace_id="trace-1",
        rubric_name="authorization_bypass",
        success_threshold=4.5,
    )

    assert len(cases) == 1
    assert scores == [1.0]
    assert len(records) == 1
    assert records[0].seam == "defense.replay"
    assert records[0].role == "defense_validator"
    assert records[0].evidence_class == "live_replay"
    assert records[0].metadata["case_id"] == "exploit-1"
