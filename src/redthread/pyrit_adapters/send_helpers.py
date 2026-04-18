from __future__ import annotations

from typing import Any

from redthread.pyrit_adapters.execution_records import ExecutionMetadata


async def send_with_execution_metadata(
    target: Any,
    *,
    prompt: str,
    conversation_id: str = "",
    execution_metadata: ExecutionMetadata | None = None,
) -> str:
    """Call target.send() with execution metadata when the target supports it."""
    try:
        return await target.send(
            prompt=prompt,
            conversation_id=conversation_id,
            execution_metadata=execution_metadata,
        )
    except TypeError as exc:
        if "execution_metadata" not in str(exc):
            raise
        return await target.send(prompt=prompt, conversation_id=conversation_id)


async def send_with_usage_and_execution_metadata(
    target: Any,
    *,
    prompt: str,
    conversation_id: str = "",
    execution_metadata: ExecutionMetadata | None = None,
) -> tuple[str, int]:
    try:
        return await target.send_with_usage(
            prompt=prompt,
            conversation_id=conversation_id,
            execution_metadata=execution_metadata,
        )
    except TypeError as exc:
        if "execution_metadata" not in str(exc):
            raise
        return await target.send_with_usage(prompt=prompt, conversation_id=conversation_id)
