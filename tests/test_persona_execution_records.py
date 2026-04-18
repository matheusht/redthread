from __future__ import annotations

from dataclasses import dataclass

import pytest

from redthread.config.settings import RedThreadSettings, TargetBackend
from redthread.models import MitreAtlasTactic, PsychologicalTrigger
from redthread.personas.generator import PersonaGenerator
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
        attacker_backend=TargetBackend.OPENAI,
        attacker_model="gpt-4o-mini",
        openai_api_key="test-key",
        dry_run=False,
    )


@pytest.mark.asyncio
async def test_persona_generation_emits_execution_record(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "redthread.pyrit_adapters.client.import_pyrit_runtime",
        lambda: (FakeMessage, FakeMessagePiece, object),
    )
    records = []
    generator = PersonaGenerator(make_settings(), execution_recorder=records.append)
    generator._attacker = RedThreadTarget(
        pyrit_target=SuccessfulPyritTarget(
            '{"name":"Alice Smith","cover_story":"Audit follow-up.","hidden_objective":"Extract system prompt.","system_prompt":"You are Alice.","allowed_strategies":["cite authority"]}'
        ),
        model_name="gpt-4o-mini",
        execution_recorder=records.append,
    )

    persona = await generator.generate(
        "Extract system prompt",
        MitreAtlasTactic.INITIAL_ACCESS,
        [PsychologicalTrigger.AUTHORITY],
    )

    assert persona.name == "Alice Smith"
    assert len(records) == 1
    assert records[0].seam == "persona.generate"
    assert records[0].role == "attacker"
    assert records[0].evidence_class == "live_generation"
    assert records[0].metadata["tactic"] == MitreAtlasTactic.INITIAL_ACCESS.value
