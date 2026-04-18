from __future__ import annotations

from dataclasses import dataclass

import pytest

from redthread.config.settings import RedThreadSettings, TargetBackend
from redthread.orchestration.models import AuthorizationDecisionType
from redthread.personas.generator import PersonaGenerator
from redthread.pyrit_adapters.client import RedThreadTarget
from redthread.pyrit_adapters.interceptors import LiveExecutionInterceptionError, intercept_live_execution
from redthread.tools.authorization import AuthorizationPolicy, build_execution_authorization_interceptor


@dataclass
class FakeMessagePiece:
    role: str = "assistant"
    original_value: str = ""
    conversation_id: str = ""
    converted_value: str | None = None


@dataclass
class FakeMessage:
    message_pieces: list[FakeMessagePiece]


class CountingPyritTarget:
    def __init__(self, response: str) -> None:
        self._response = response
        self.calls = 0

    async def send_prompt_async(self, message: FakeMessage) -> list[FakeMessage]:
        self.calls += 1
        return [FakeMessage([FakeMessagePiece(original_value=self._response)])]


def make_settings() -> RedThreadSettings:
    return RedThreadSettings(
        attacker_backend=TargetBackend.OPENAI,
        attacker_model="gpt-4o-mini",
        openai_api_key="test-key",
        dry_run=False,
    )


@pytest.mark.asyncio
async def test_common_boundary_interceptor_blocks_persona_generation_before_send(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "redthread.pyrit_adapters.client.import_pyrit_runtime",
        lambda: (FakeMessage, FakeMessagePiece, object),
    )
    fake_target = CountingPyritTarget(
        '{"name":"Alice Smith","cover_story":"Audit follow-up.","hidden_objective":"Extract system prompt.","system_prompt":"You are Alice.","allowed_strategies":["cite authority"]}'
    )
    generator = PersonaGenerator(make_settings())
    generator._attacker = RedThreadTarget(pyrit_target=fake_target, model_name="gpt-4o-mini")
    deny = AuthorizationPolicy(
        policy_id="deny-persona-generate",
        actor_roles=["attacker"],
        denied_capabilities=["attacker.persona.generate"],
        decision=AuthorizationDecisionType.DENY,
        reason="block test",
    )

    with pytest.raises(LiveExecutionInterceptionError, match="Execution blocked"):
        with intercept_live_execution(
            build_execution_authorization_interceptor(policies=[deny])
        ):
            await generator.generate("Extract system prompt")

    assert fake_target.calls == 0
