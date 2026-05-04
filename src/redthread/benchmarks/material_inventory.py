"""Prompt-safe benchmark material vault inventory."""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, Field

from redthread.benchmarks.material_vault import (
    MaterialVaultError,
    benchmark_material_root,
    load_material_manifest,
    safe_vault_path,
    sha256_file,
)


class BenchmarkMaterialInventoryRow(BaseModel):
    """One prompt-safe material manifest inventory row."""

    manifest_ref: str = Field(min_length=1)
    fixture_id: str = Field(min_length=1)
    material_ref: str = Field(min_length=1)
    material_class: str = Field(min_length=1)
    review_status: str = Field(min_length=1)
    reviewers: list[str] = Field(default_factory=list)
    allowed_target_ids: list[str] = Field(default_factory=list)
    source_path: str = Field(min_length=1)
    source_commit: str = Field(min_length=1)
    hash_verified: bool = False
    hash_status: str = "not_checked"


class BenchmarkMaterialInventory(BaseModel):
    """Prompt-safe vault inventory payload."""

    material_root: str = Field(min_length=1)
    collection_id: str | None = None
    material_class: str | None = None
    allowed_target_id: str | None = None
    manifest_count: int = 0
    verified_hash_count: int = 0
    invalid_hash_count: int = 0
    manifests: list[BenchmarkMaterialInventoryRow] = Field(default_factory=list)
    raw_prompt_policy: str = "raw prompt bodies stay in the private benchmark vault and are not read"


def list_benchmark_material_manifests(
    *,
    material_root: str | Path | None = None,
    collection_id: str | None = None,
    material_class: str | None = None,
    allowed_target_id: str | None = None,
    verify_hashes: bool = False,
) -> BenchmarkMaterialInventory:
    """List reviewed material manifests without reading prompt bodies."""
    root = benchmark_material_root(material_root)
    refs = _manifest_refs(root, collection_id)
    rows: list[BenchmarkMaterialInventoryRow] = []
    for manifest_ref in refs:
        manifest = load_material_manifest(manifest_ref, material_root=root)
        if not _matches_filters(manifest.material_class, manifest.allowed_target_ids, material_class, allowed_target_id):
            continue
        hash_status = _hash_status(root, manifest.material_ref, manifest.sha256, verify_hashes)
        rows.append(
            BenchmarkMaterialInventoryRow(
                manifest_ref=manifest_ref,
                fixture_id=manifest.fixture_id,
                material_ref=manifest.material_ref,
                material_class=manifest.material_class,
                review_status=manifest.review_status,
                reviewers=manifest.reviewers,
                allowed_target_ids=manifest.allowed_target_ids,
                source_path=manifest.source_path,
                source_commit=manifest.source_commit,
                hash_verified=hash_status == "verified",
                hash_status=hash_status,
            )
        )
    return BenchmarkMaterialInventory(
        material_root=str(root),
        collection_id=collection_id,
        material_class=material_class,
        allowed_target_id=allowed_target_id,
        manifest_count=len(rows),
        verified_hash_count=sum(1 for row in rows if row.hash_status == "verified"),
        invalid_hash_count=sum(1 for row in rows if row.hash_status in {"mismatch", "missing"}),
        manifests=rows,
    )


def _matches_filters(
    row_material_class: str,
    row_allowed_target_ids: list[str],
    material_class: str | None,
    allowed_target_id: str | None,
) -> bool:
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
