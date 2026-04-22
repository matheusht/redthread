from __future__ import annotations

from collections.abc import Sequence
from uuid import uuid4

from redthread.config.settings import RedThreadSettings, TargetBackend
from redthread.pyrit_adapters.execution_context import get_execution_recorder
from redthread.pyrit_adapters.execution_records import (
    ExecutionMetadata,
    ExecutionRecorder,
    build_execution_record,
)
from redthread.pyrit_adapters.interceptors import maybe_intercept_live_execution
from redthread.pyrit_adapters.runtime import (
    PromptChatTarget,
    PyritMessage,
    _build_pyrit_target,
    import_pyrit_runtime,
)


class RedThreadTarget:
    """Thin async wrapper around a PyRIT PromptChatTarget."""

    def __init__(
        self,
        pyrit_target: PromptChatTarget,
        model_name: str,
        execution_recorder: ExecutionRecorder | None = None,
    ) -> None:
        self._target = pyrit_target
        self.model_name = model_name
        self._execution_recorder = execution_recorder

    @classmethod
    def from_settings(
        cls,
        backend: TargetBackend,
        model: str,
        settings: RedThreadSettings,
        base_url: str | None = None,
        execution_recorder: ExecutionRecorder | None = None,
    ) -> RedThreadTarget:
        pyrit_target = _build_pyrit_target(
            backend=backend,
            model=model,
            base_url=base_url or settings.target_base_url,
            api_key=settings.openai_api_key,
        )
        return cls(pyrit_target=pyrit_target, model_name=model, execution_recorder=execution_recorder)

    async def send(
        self,
        prompt: str,
        conversation_id: str = "",
        execution_metadata: ExecutionMetadata | None = None,
    ) -> str:
        conversation_id = conversation_id or execution_metadata_id(execution_metadata)
        if not conversation_id:
            conversation_id = str(uuid4())

        try:
            maybe_intercept_live_execution(execution_metadata)
            message_cls, message_piece_cls, _ = import_pyrit_runtime()
            piece = message_piece_cls(
                role="user",
                original_value=prompt,
                conversation_id=conversation_id,
            )
            message = message_cls(message_pieces=[piece])
            response_messages = await self._target.send_prompt_async(message=message)
            response = _extract_response_text(response_messages)
        except Exception as exc:
            self._record_execution(
                conversation_id=conversation_id,
                execution_metadata=execution_metadata,
                success=False,
                error=f"{type(exc).__name__}: {exc}",
            )
            raise

        self._record_execution(
            conversation_id=conversation_id,
            execution_metadata=execution_metadata,
            success=True,
        )
        return response

    async def send_with_usage(
        self,
        prompt: str,
        conversation_id: str = "",
        execution_metadata: ExecutionMetadata | None = None,
    ) -> tuple[str, int]:
        response = await self.send(prompt, conversation_id, execution_metadata=execution_metadata)
        return response, (len(prompt) + len(response)) // 4

    def close(self) -> None:
        if hasattr(self._target, "dispose_db_engine"):
            try:
                self._target.dispose_db_engine()  # type: ignore[attr-defined]
            except Exception:
                pass

    def _record_execution(
        self,
        *,
        conversation_id: str,
        execution_metadata: ExecutionMetadata | None,
        success: bool,
        error: str | None = None,
    ) -> None:
        recorder = self._execution_recorder or get_execution_recorder()
        if recorder is None or execution_metadata is None:
            return
        recorder(
            build_execution_record(
                model_name=self.model_name,
                conversation_id=conversation_id,
                execution_metadata=execution_metadata,
                success=success,
                error=error,
            )
        )


def execution_metadata_id(execution_metadata: ExecutionMetadata | None) -> str:
    if execution_metadata is None or execution_metadata.conversation_id is None:
        return ""
    return execution_metadata.conversation_id


def _extract_response_text(response_messages: Sequence[PyritMessage]) -> str:
    if not response_messages:
        return ""
    first_message = response_messages[0]
    if not first_message.message_pieces:
        return ""
    first_piece = first_message.message_pieces[0]
    return first_piece.converted_value or first_piece.original_value
