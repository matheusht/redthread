from __future__ import annotations

from dataclasses import replace
from typing import Any

from redthread.orchestration.canary_containment import evaluate_canary_containment
from redthread.pyrit_adapters.execution_records import ExecutionMetadata
from redthread.pyrit_adapters.interceptors import LiveExecutionInterceptionError


async def send_with_execution_metadata(
    target: Any,
    *,
    prompt: str,
    conversation_id: str = "",
    execution_metadata: ExecutionMetadata | None = None,
) -> str:
    """Call target.send() with execution metadata when the target supports it."""
    execution_metadata = _with_canary_decision(prompt, execution_metadata)
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
    execution_metadata = _with_canary_decision(prompt, execution_metadata)
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


def _with_canary_decision(
    prompt: str,
    execution_metadata: ExecutionMetadata | None,
) -> ExecutionMetadata | None:
    if execution_metadata is None:
        return None
    decision = evaluate_canary_containment(
        seam=execution_metadata.seam,
        prompt=prompt,
        metadata=execution_metadata.metadata,
        canary_tags=execution_metadata.canary_tags,
    )
    updated_tags = list(dict.fromkeys([*execution_metadata.canary_tags, *decision.canary_tags]))
    updated_metadata = replace(
        execution_metadata,
        canary_tags=updated_tags,
        canary_containment=decision.model_dump(mode="json"),
    )
    if decision.blocked:
        raise LiveExecutionInterceptionError(decision.reason)
    return updated_metadata
