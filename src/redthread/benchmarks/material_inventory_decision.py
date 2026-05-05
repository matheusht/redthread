"""Engine-calculated benchmark material inventory decisions."""

from __future__ import annotations

import shlex
from collections.abc import Iterable

from redthread.benchmarks.material_inventory_models import BenchmarkMaterialInventoryRow


def material_inventory_engine_decision(rows: list[BenchmarkMaterialInventoryRow]) -> str:
    """Return the operator-facing inventory readiness state."""
    if not rows:
        return "empty_inventory"
    if any(material_inventory_row_is_blocked(row) for row in rows):
        return "blocked"
    if any(row.hash_status == "not_checked" for row in rows):
        return "needs_hash_check"
    if not any(material_inventory_row_is_ready(row) for row in rows):
        return "no_replay_ready"
    return "ready_for_replay"


def material_inventory_blocked_reason_counts(rows: Iterable[BenchmarkMaterialInventoryRow]) -> dict[str, int]:
    """Return prompt-safe blocked reason counts for inventory rows."""
    counts: dict[str, int] = {}
    for row in rows:
        for reason in _blocked_reasons(row):
            counts[reason] = counts.get(reason, 0) + 1
    return counts


def material_inventory_operator_next_step(engine_decision: str) -> str:
    """Return a low-friction next step derived from engine state."""
    if engine_decision == "ready_for_replay":
        return "ready for approved local replay"
    if engine_decision == "blocked":
        return "fix invalid hashes or review gates before replay"
    if engine_decision == "empty_inventory":
        return "import reviewed material before replay"
    if engine_decision == "no_replay_ready":
        return "import approved replay seed before replay"
    return "verify hashes before replay"


def material_inventory_suggested_replay_commands(
    rows: Iterable[BenchmarkMaterialInventoryRow],
    *,
    material_root: str | None = None,
) -> list[str]:
    """Return prompt-safe local replay commands for ready rows."""
    commands: list[str] = []
    root_arg = f" --material-root {shlex.quote(material_root)}" if material_root else ""
    for row in rows:
        if not material_inventory_row_is_ready(row):
            continue
        source_arg = _source_arg(row.source_path)
        commands.append(
            "redthread eval jailbreak-corpus --replay "
            f"{source_arg}--fixture-id {shlex.quote(row.fixture_id)} --manifest-ref {shlex.quote(row.manifest_ref)}"
            f"{root_arg}"
        )
    return commands


def _source_arg(source_path: str) -> str:
    if source_path.startswith("metadata-only/jailbreakbench"):
        return "--source jailbreakbench "
    return ""


def material_inventory_operator_summary(
    *,
    engine_decision: str,
    ready_count: int,
    blocked_count: int,
) -> str:
    """Return a concise prompt-safe summary for operators."""
    if engine_decision == "ready_for_replay":
        return f"ready={ready_count}; blocked=0; no operator action needed"
    if engine_decision == "blocked":
        return f"ready={ready_count}; blocked={blocked_count}; fix blockers before replay"
    if engine_decision == "empty_inventory":
        return "ready=0; blocked=0; import reviewed material"
    if engine_decision == "no_replay_ready":
        return "ready=0; blocked=0; import approved replay seed"
    return f"ready={ready_count}; blocked={blocked_count}; hash check needed"


def material_inventory_row_is_ready(row: BenchmarkMaterialInventoryRow) -> bool:
    """Return whether one prompt-safe inventory row is replay-ready."""
    return row.material_class == "approved_replay_seed" and row.review_gate_status == "two_reviewer_gate_met" and row.hash_status == "verified"


def material_inventory_row_is_blocked(row: BenchmarkMaterialInventoryRow) -> bool:
    """Return whether one prompt-safe inventory row blocks replay."""
    return bool(_blocked_reasons(row))


def _blocked_reasons(row: BenchmarkMaterialInventoryRow) -> list[str]:
    reasons: list[str] = []
    if row.hash_status == "mismatch":
        reasons.append("hash_mismatch")
    if row.hash_status == "missing":
        reasons.append("material_missing")
    if row.review_gate_status == "two_reviewer_gate_failed":
        reasons.append("review_gate_failed")
    return reasons
