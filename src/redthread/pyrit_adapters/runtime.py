from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from redthread.config.settings import TargetBackend

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pyrit.models.message import Message as PyritMessage
    from pyrit.models.message_piece import MessagePiece as PyritMessagePiece
    from pyrit.prompt_target.common.prompt_chat_target import PromptChatTarget
    from pyrit.prompt_target.openai.openai_chat_target import (
        OpenAIChatTarget as PyritOpenAIChatTarget,
    )
else:
    PromptChatTarget = Any
    PyritMessage = Any
    PyritMessagePiece = Any
    PyritOpenAIChatTarget = Any

_pyrit_memory_initialized = False


def import_pyrit_runtime() -> tuple[type[PyritMessage], type[PyritMessagePiece], type[PyritOpenAIChatTarget]]:
    from pyrit.models import Message
    from pyrit.models.message_piece import MessagePiece
    from pyrit.prompt_target import OpenAIChatTarget

    return Message, MessagePiece, OpenAIChatTarget


def ensure_pyrit_memory_initialized(db_dir: Path | None = None) -> None:
    global _pyrit_memory_initialized
    if _pyrit_memory_initialized:
        return

    from pyrit.memory import CentralMemory, SQLiteMemory

    db_path = (db_dir or Path("./logs")) / ".pyrit_memory.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    CentralMemory.set_memory_instance(SQLiteMemory(db_path=db_path))
    _pyrit_memory_initialized = True
    logger.debug("PyRIT CentralMemory initialized at %s", db_path)


def _build_pyrit_target(
    backend: TargetBackend,
    model: str,
    base_url: str,
    api_key: str = "",
    max_tokens: int = 2048,
) -> PromptChatTarget:
    ensure_pyrit_memory_initialized()
    if api_key:
        os.environ["OPENAI_CHAT_KEY"] = api_key

    _, _, openai_chat_target_cls = import_pyrit_runtime()
    if backend == TargetBackend.OLLAMA:
        return _build_ollama_target(openai_chat_target_cls, model, base_url, max_tokens)
    if backend == TargetBackend.OPENAI:
        return cast(
            PromptChatTarget,
            openai_chat_target_cls(
                model_name=model,
                endpoint="https://api.openai.com/v1",
                api_key=api_key,
                max_tokens=max_tokens,
            ),
        )
    if backend == TargetBackend.LLAMA_CPP:
        return cast(
            PromptChatTarget,
            openai_chat_target_cls(
                model_name=model,
                endpoint=f"{base_url.rstrip('/')}/v1",
                api_key="llama-cpp",
                max_tokens=max_tokens,
            ),
        )
    raise ValueError(f"Unsupported backend: {backend}")


def _build_ollama_target(
    openai_chat_target_cls: type[PyritOpenAIChatTarget],
    model: str,
    base_url: str,
    max_tokens: int,
) -> PromptChatTarget:
    normalized_url = base_url.rstrip("/")
    extra_headers: dict[str, str] = {}
    if "ngrok" in normalized_url:
        extra_headers["ngrok-skip-browser-warning"] = "true"
    if "pinggy" in normalized_url:
        extra_headers["x-pinggy-no-screen"] = "true"
    return cast(
        PromptChatTarget,
        openai_chat_target_cls(
            model_name=model,
            endpoint=f"{normalized_url}/v1",
            api_key="ollama",
            max_tokens=max_tokens,
            headers=json.dumps(extra_headers) if extra_headers else None,
        ),
    )
