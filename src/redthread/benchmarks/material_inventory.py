"""Prompt-safe benchmark material vault inventory."""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, Field

from redthread.benchmarks.material_vault import (
    MaterialVaultError,
    benchmark_material_root,
    load_material_manifest,
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


class BenchmarkMaterialInventory(BaseModel):
    """Prompt-safe vault inventory payload."""

    material_root: str = Field(min_length=1)
    collection_id: str | None = None
    manifest_count: int = 0
    manifests: list[BenchmarkMaterialInventoryRow] = Field(default_factory=list)
    raw_prompt_policy: str = "raw prompt bodies stay in the private benchmark vault and are not read"


def list_benchmark_material_manifests(
    *,
    material_root: str | Path | None = None,
    collection_id: str | None = None,
) -> BenchmarkMaterialInventory:
    """List reviewed material manifests without reading prompt bodies."""
    root = benchmark_material_root(material_root)
    refs = _manifest_refs(root, collection_id)
    rows: list[BenchmarkMaterialInventoryRow] = []
    for manifest_ref in refs:
        manifest = load_material_manifest(manifest_ref, material_root=root)
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
            )
        )
    return BenchmarkMaterialInventory(
        material_root=str(root),
        collection_id=collection_id,
        manifest_count=len(rows),
        manifests=rows,
    )


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
