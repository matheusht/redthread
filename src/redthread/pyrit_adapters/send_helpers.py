from __future__ import annotations

import logging
from dataclasses import replace
from typing import Any

from redthread.orchestration.canary_containment import evaluate_canary_containment
from redthread.pyrit_adapters.capabilities import CapabilityRequirement
from redthread.pyrit_adapters.execution_context import get_execution_recorder
from redthread.pyrit_adapters.execution_records import ExecutionMetadata, build_execution_record
from redthread.pyrit_adapters.interceptors import LiveExecutionInterceptionError

logger = logging.getLogger(__name__)


async def send_with_execution_metadata(
    target: Any,
    *,
    prompt: str,
    conversation_id: str = "",
    execution_metadata: ExecutionMetadata | None = None,
    capability_requirement: CapabilityRequirement | None = None,
) -> str:
    """Call target.send() with execution metadata when the target supports it."""
    execution_metadata = _with_canary_decision(prompt, execution_metadata)
    send_kwargs: dict[str, Any] = {
        "prompt": prompt,
        "conversation_id": conversation_id,
        "execution_metadata": execution_metadata,
    }
    if capability_requirement is not None:
        send_kwargs["capability_requirement"] = capability_requirement
    try:
        return await target.send(**send_kwargs)
    except TypeError as exc:
        if "execution_metadata" not in str(exc):
            raise
        _record_fallback(target, conversation_id, execution_metadata)
        return await target.send(prompt=prompt, conversation_id=conversation_id)


async def send_with_usage_and_execution_metadata(
    target: Any,
    *,
    prompt: str,
    conversation_id: str = "",
    execution_metadata: ExecutionMetadata | None = None,
    capability_requirement: CapabilityRequirement | None = None,
) -> tuple[str, int]:
    execution_metadata = _with_canary_decision(prompt, execution_metadata)
    send_kwargs: dict[str, Any] = {
        "prompt": prompt,
        "conversation_id": conversation_id,
        "execution_metadata": execution_metadata,
    }
    if capability_requirement is not None:
        send_kwargs["capability_requirement"] = capability_requirement
    try:
        return await target.send_with_usage(**send_kwargs)
    except TypeError as exc:
        if "execution_metadata" not in str(exc):
            raise
        _record_fallback(target, conversation_id, execution_metadata)
        return await target.send_with_usage(prompt=prompt, conversation_id=conversation_id)


def _record_fallback(
    target: Any,
    conversation_id: str,
    execution_metadata: ExecutionMetadata | None,
) -> None:
    if execution_metadata is None:
        return
    recorder = get_execution_recorder()
    if recorder is not None:
        fallback_meta = replace(
            execution_metadata,
            metadata={**dict(execution_metadata.metadata), "signature_fallback": True},
        )
        recorder(
            build_execution_record(
                model_name=getattr(target, "model_name", "unknown"),
                conversation_id=conversation_id,
                execution_metadata=fallback_meta,
                success=True,
            )
        )


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
        mode=str(
            execution_metadata.metadata.get("canary_policy_preset", "block_memory_and_outbound")
        ),
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
