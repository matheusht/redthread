"""Engine-calculated benchmark material inventory decisions."""

from __future__ import annotations

from redthread.benchmarks.material_inventory_models import BenchmarkMaterialInventoryRow


def material_inventory_engine_decision(rows: list[BenchmarkMaterialInventoryRow]) -> str:
    """Return the operator-facing inventory readiness state."""
    if not rows:
        return "empty_inventory"
    if any(material_inventory_row_is_blocked(row) for row in rows):
        return "blocked"
    if any(row.hash_status == "not_checked" for row in rows):
        return "needs_hash_check"
    return "ready_for_replay"


def material_inventory_operator_next_step(engine_decision: str) -> str:
    """Return a low-friction next step derived from engine state."""
    if engine_decision == "ready_for_replay":
        return "ready for approved local replay"
    if engine_decision == "blocked":
        return "fix invalid hashes or review gates before replay"
    if engine_decision == "empty_inventory":
        return "import reviewed material before replay"
    return "verify hashes before replay"


def material_inventory_row_is_ready(row: BenchmarkMaterialInventoryRow) -> bool:
    """Return whether one prompt-safe inventory row is replay-ready."""
    gate_ready = row.review_gate_status in {"not_required", "two_reviewer_gate_met"}
    return gate_ready and row.hash_status == "verified"


def material_inventory_row_is_blocked(row: BenchmarkMaterialInventoryRow) -> bool:
    """Return whether one prompt-safe inventory row blocks replay."""
    return row.hash_status in {"mismatch", "missing"} or row.review_gate_status == "two_reviewer_gate_failed"
