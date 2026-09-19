"""Preflight capability and canary containment guards for RedThreadTarget."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from redthread.orchestration.canary_containment import evaluate_canary_containment
from redthread.pyrit_adapters.capabilities import (
    CapabilityRequirement,
    UnsupportedTargetCapabilityError,
    check_requirement,
    from_pyrit_target,
)
from redthread.pyrit_adapters.execution_records import ExecutionMetadata


def apply_canary_containment(
    prompt: str,
    execution_metadata: ExecutionMetadata | None,
) -> ExecutionMetadata | None:
    """Evaluate canary containment and update execution metadata or raise if blocked."""
    if execution_metadata is None:
        return None
    if execution_metadata.canary_containment is not None:
        return execution_metadata
    decision = evaluate_canary_containment(
        seam=execution_metadata.seam,
        prompt=prompt,
        metadata=execution_metadata.metadata,
        canary_tags=execution_metadata.canary_tags,
    )
    updated = replace(
        execution_metadata,
        canary_tags=list(dict.fromkeys([*execution_metadata.canary_tags, *decision.canary_tags])),
        canary_containment=decision.model_dump(mode="json"),
    )
    if decision.blocked:
        raise RuntimeError(decision.reason)
    return updated


def apply_capability_preflight(
    pyrit_target: Any,
    execution_metadata: ExecutionMetadata | None,
    requirement: CapabilityRequirement | None,
) -> tuple[ExecutionMetadata | None, UnsupportedTargetCapabilityError | None]:
    """Check target capabilities before execution; attach diagnostic metadata on failure."""
    capabilities = from_pyrit_target(pyrit_target)
    check = check_requirement(capabilities, requirement)
    if check.supported:
        return execution_metadata, None

    detail = {
        **check.as_metadata(),
        "failure_stage": "capability_preflight",
        "provider_call": False,
        "requirement": (requirement or CapabilityRequirement()).as_metadata(),
        "target_capabilities": capabilities.as_metadata(),
    }
    if execution_metadata is not None:
        execution_metadata = replace(
            execution_metadata,
            metadata={**dict(execution_metadata.metadata), "capability_preflight": detail},
        )
    return execution_metadata, UnsupportedTargetCapabilityError(check.reason)
