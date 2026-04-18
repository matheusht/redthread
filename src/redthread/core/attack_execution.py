from __future__ import annotations

from typing import Any

from redthread.pyrit_adapters.targets import ExecutionMetadata


def attack_execution_metadata(
    *,
    algorithm: str,
    lane: str,
    trace_id: str,
    metadata: dict[str, Any] | None = None,
) -> ExecutionMetadata:
    role = "attacker" if "attacker" in lane else "target"
    evidence_class = "live_generation" if role == "attacker" else "live_attack_execution"
    combined = {"algorithm": algorithm, "trace_id": trace_id}
    if metadata:
        combined.update(metadata)
    return ExecutionMetadata(
        seam=f"attack.{algorithm}.{lane}",
        role=role,
        evidence_class=evidence_class,
        metadata=combined,
    )
