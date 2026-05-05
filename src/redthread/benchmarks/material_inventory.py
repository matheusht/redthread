"""Prompt-safe benchmark material vault inventory."""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from redthread.benchmarks.material_inventory_models import (
    BenchmarkMaterialInventory,
    BenchmarkMaterialInventoryRow,
)
from redthread.benchmarks.material_vault import (
    MaterialVaultError,
    benchmark_material_root,
    load_material_manifest,
    safe_vault_path,
    sha256_file,
)


def list_benchmark_material_manifests(
    *,
    material_root: str | Path | None = None,
    collection_id: str | None = None,
    fixture_id: str | None = None,
    material_class: str | None = None,
    allowed_target_id: str | None = None,
    review_gate_status: str | None = None,
    limit: int | None = None,
    verify_hashes: bool = False,
    invalid_hashes_only: bool = False,
) -> BenchmarkMaterialInventory:
    """List reviewed material manifests without returning prompt bodies."""
    root = benchmark_material_root(material_root)
    should_verify_hashes = verify_hashes or invalid_hashes_only
    if limit is not None and limit < 1:
        msg = "material inventory limit must be at least 1"
        raise MaterialVaultError(msg)
    refs = _manifest_refs(root, collection_id)
    rows: list[BenchmarkMaterialInventoryRow] = []
    for manifest_ref in refs:
        manifest = load_material_manifest(manifest_ref, material_root=root)
        if not _matches_filters(
            manifest.fixture_id,
            manifest.material_class,
            manifest.allowed_target_ids,
            fixture_id,
            material_class,
            allowed_target_id,
        ):
            continue
        gate_status = _review_gate_status(manifest.material_class, manifest.reviewers)
        if review_gate_status is not None and gate_status != review_gate_status:
            continue
        hash_status = _hash_status(root, manifest.material_ref, manifest.sha256, should_verify_hashes)
        if invalid_hashes_only and hash_status not in {"mismatch", "missing"}:
            continue
        if limit is not None and len(rows) >= limit:
            break
        rows.append(
            BenchmarkMaterialInventoryRow(
                manifest_ref=manifest_ref,
                collection_id=_collection_id_from_ref(manifest_ref),
                fixture_id=manifest.fixture_id,
                material_ref=manifest.material_ref,
                material_class=manifest.material_class,
                review_status=manifest.review_status,
                reviewers=manifest.reviewers,
                reviewer_count=len(manifest.reviewers),
                review_gate_status=gate_status,
                allowed_target_ids=manifest.allowed_target_ids,
                source_path=manifest.source_path,
                source_commit=manifest.source_commit,
                hash_verified=hash_status == "verified",
                hash_status=hash_status,
            )
        )
    engine_decision = _engine_decision(rows)
    return BenchmarkMaterialInventory(
        material_root=str(root),
        collection_id=collection_id,
        fixture_id=fixture_id,
        material_class=material_class,
        allowed_target_id=allowed_target_id,
        review_gate_status=review_gate_status,
        limit=limit,
        invalid_hashes_only=invalid_hashes_only,
        manifest_count=len(rows),
        verified_hash_count=sum(1 for row in rows if row.hash_status == "verified"),
        invalid_hash_count=sum(1 for row in rows if row.hash_status in {"mismatch", "missing"}),
        material_ready_count=sum(1 for row in rows if _row_is_ready(row)),
        material_blocked_count=sum(1 for row in rows if _row_is_blocked(row)),
        engine_decision=engine_decision,
        operator_next_step=_operator_next_step(engine_decision),
        collection_counts=_count_values(row.collection_id for row in rows),
        material_class_counts=_count_values(row.material_class for row in rows),
        hash_status_counts=_count_values(row.hash_status for row in rows),
        review_gate_counts=_count_values(row.review_gate_status for row in rows),
        allowed_target_counts=_count_values(target for row in rows for target in row.allowed_target_ids),
        manifests=rows,
    )


def _collection_id_from_ref(manifest_ref: str) -> str:
    return manifest_ref.split("/", maxsplit=1)[0]


def _engine_decision(rows: list[BenchmarkMaterialInventoryRow]) -> str:
    if not rows:
        return "empty_inventory"
    if any(_row_is_blocked(row) for row in rows):
        return "blocked"
    if any(row.hash_status == "not_checked" for row in rows):
        return "needs_hash_check"
    return "ready_for_replay"


def _operator_next_step(engine_decision: str) -> str:
    if engine_decision == "ready_for_replay":
        return "ready for approved local replay"
    if engine_decision == "blocked":
        return "fix invalid hashes or review gates before replay"
    if engine_decision == "empty_inventory":
        return "import reviewed material before replay"
    return "verify hashes before replay"


def _row_is_ready(row: BenchmarkMaterialInventoryRow) -> bool:
    gate_ready = row.review_gate_status in {"not_required", "two_reviewer_gate_met"}
    return gate_ready and row.hash_status == "verified"


def _row_is_blocked(row: BenchmarkMaterialInventoryRow) -> bool:
    return row.hash_status in {"mismatch", "missing"} or row.review_gate_status == "two_reviewer_gate_failed"


def _review_gate_status(material_class: str, reviewers: list[str]) -> str:
    if material_class != "approved_replay_seed":
        return "not_required"
    if len({reviewer.strip() for reviewer in reviewers if reviewer.strip()}) >= 2:
        return "two_reviewer_gate_met"
    return "two_reviewer_gate_failed"


def _count_values(values: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _matches_filters(
    row_fixture_id: str,
    row_material_class: str,
    row_allowed_target_ids: list[str],
    fixture_id: str | None,
    material_class: str | None,
    allowed_target_id: str | None,
) -> bool:
    if fixture_id is not None and row_fixture_id != fixture_id:
        return False
    if material_class is not None and row_material_class != material_class:
        return False
    return not (allowed_target_id is not None and allowed_target_id not in row_allowed_target_ids)


def _hash_status(root: Path, material_ref: str, expected_sha256: str, verify_hashes: bool) -> str:
    if not verify_hashes:
        return "not_checked"
    material_path = safe_vault_path(root, material_ref)
    if not material_path.is_file():
        return "missing"
    digest = sha256_file(material_path)
    if digest != expected_sha256:
        return "mismatch"
    return "verified"


def _manifest_refs(root: Path, collection_id: str | None) -> list[str]:
    if collection_id is not None:
        _validate_collection_id(collection_id)
        manifest_paths = sorted((root / collection_id / "manifests").glob("*.json"))
    else:
        manifest_paths = sorted(root.glob("*/manifests/*.json"))
    return [path.relative_to(root).as_posix() for path in manifest_paths if path.is_file()]


def _validate_collection_id(collection_id: str) -> None:
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", collection_id):
        msg = "collection id must be a safe slug"
        raise MaterialVaultError(msg)
