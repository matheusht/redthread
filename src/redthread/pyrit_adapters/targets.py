"""PyRIT adapter — wraps PyRIT 0.12.0's target interface into a simple async send().

PyRIT 0.12.0 API (verified against installed version):
  - Target construction: OpenAITarget(model_name=, endpoint=, api_key=) kwargs
  - OpenAIChatTarget(model_name=..., **kwargs) inherits from OpenAITarget
  - Send: await target.send_prompt_async(message=Message([MessagePiece(role=, original_value=)]))
  - Message is built from MessagePiece objects via pyrit.models

This is the ONLY file in RedThread that imports PyRIT directly.
All other modules use the RedThreadTarget wrapper.

Supported backends:
  - Ollama (local, localhost:11434) — attacker + target during development
  - OpenAI — judge (gpt-4o), and production attacker (gpt-4o-mini)
"""

from __future__ import annotations

import logging
from uuid import uuid4

from pyrit.models import Message
from pyrit.models.message_piece import MessagePiece
from pyrit.models import ChatMessageRole
from pyrit.prompt_target import OpenAIChatTarget, PromptChatTarget

from redthread.config.settings import RedThreadSettings, TargetBackend

logger = logging.getLogger(__name__)


def _build_pyrit_target(
    backend: TargetBackend,
    model: str,
    base_url: str,
    api_key: str = "",
) -> PromptChatTarget:
    """Factory — instantiate the correct PyRIT target class for each backend."""

    if backend == TargetBackend.OLLAMA:
        # Ollama exposes an OpenAI-compatible /v1 endpoint
        return OpenAIChatTarget(
            model_name=model,
            endpoint=f"{base_url}/v1",
            api_key="ollama",  # Ollama ignores the key but OpenAITarget requires non-empty
        )
    elif backend == TargetBackend.OPENAI:
        return OpenAIChatTarget(
            model_name=model,
            api_key=api_key,
        )
    else:
        raise ValueError(f"Unsupported backend: {backend}")


class RedThreadTarget:
    """Thin async wrapper around a PyRIT PromptChatTarget.

    Exposes a single `async send(prompt: str) -> str` interface so that
    algorithm code (PAIR, TAP, etc.) never imports PyRIT directly.
    """

    def __init__(self, pyrit_target: PromptChatTarget, model_name: str) -> None:
        self._target = pyrit_target
        self.model_name = model_name

    @classmethod
    def from_settings(
        cls,
        backend: TargetBackend,
        model: str,
        settings: RedThreadSettings,
        base_url: str | None = None,
    ) -> "RedThreadTarget":
        pyrit_target = _build_pyrit_target(
            backend=backend,
            model=model,
            base_url=base_url or settings.target_base_url,
            api_key=settings.openai_api_key,
        )
        return cls(pyrit_target=pyrit_target, model_name=model)

    async def send(self, prompt: str, conversation_id: str = "") -> str:
        """Send a prompt and return the target's text response.

        Uses PyRIT 0.12.0's send_prompt_async(message=Message([MessagePiece(...)]))
        """
        if not conversation_id:
            conversation_id = str(uuid4())

        piece = MessagePiece(
            role=ChatMessageRole.USER,
            original_value=prompt,
            conversation_id=conversation_id,
        )
        message = Message(message_pieces=[piece])

        response_messages: list[Message] = await self._target.send_prompt_async(
            message=message
        )

        # Extract text from first response message piece
        if response_messages and response_messages[0].message_pieces:
            first_piece = response_messages[0].message_pieces[0]
            return first_piece.converted_value or first_piece.original_value

        return ""

    def close(self) -> None:
        """Release PyRIT target resources if applicable."""
        if hasattr(self._target, "dispose_db_engine"):
            try:
                self._target.dispose_db_engine()  # type: ignore[attr-defined]
            except Exception:
                pass


def build_target(settings: RedThreadSettings) -> RedThreadTarget:
    """Build the target LLM adapter (subject under test) from settings."""
    return RedThreadTarget.from_settings(
        backend=settings.target_backend,
        model=settings.target_model,
        settings=settings,
        base_url=settings.target_base_url,
    )


def build_attacker(settings: RedThreadSettings) -> RedThreadTarget:
    """Build the attacker LLM adapter (lightweight creative engine) from settings."""
    return RedThreadTarget.from_settings(
        backend=settings.attacker_backend,
        model=settings.attacker_model,
        settings=settings,
        base_url=settings.attacker_base_url,
    )


def build_judge_llm(settings: RedThreadSettings) -> RedThreadTarget:
    """Build the judge LLM adapter (heavyweight — GPT-4o) from settings."""
    return RedThreadTarget.from_settings(
        backend=settings.judge_backend,
        model=settings.judge_model,
        settings=settings,
    )
