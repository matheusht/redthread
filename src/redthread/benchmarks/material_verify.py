"""Prompt-safe reviewed benchmark material verification."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from redthread.benchmarks.material_vault import (
    MaterialVaultError,
    benchmark_material_root,
    load_material_manifest,
    safe_vault_path,
    sha256_file,
)


class BenchmarkMaterialVerification(BaseModel):
    """Prompt-safe manifest verification result."""

    manifest_ref: str = Field(min_length=1)
    fixture_id: str = Field(min_length=1)
    material_ref: str = Field(min_length=1)
    material_class: str = Field(min_length=1)
    review_status: str = Field(min_length=1)
    reviewers: list[str] = Field(default_factory=list)
    allowed_target_ids: list[str] = Field(default_factory=list)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    hash_verified: bool = True
    raw_prompt_policy: str = "raw prompt body stays in private benchmark vault and is not printed"


def verify_benchmark_material_manifest(
    manifest_ref: str,
    *,
    material_root: str | Path | None = None,
) -> BenchmarkMaterialVerification:
    """Verify manifest hash without returning raw prompt material."""
    root = benchmark_material_root(material_root)
    manifest = load_material_manifest(manifest_ref, material_root=root)
    material_path = safe_vault_path(root, manifest.material_ref)
    digest = sha256_file(material_path)
    if digest != manifest.sha256:
        msg = "prompt material hash does not match manifest"
        raise MaterialVaultError(msg)
    return BenchmarkMaterialVerification(
        manifest_ref=manifest_ref,
        fixture_id=manifest.fixture_id,
        material_ref=manifest.material_ref,
        material_class=manifest.material_class,
        review_status=manifest.review_status,
        reviewers=manifest.reviewers,
        allowed_target_ids=manifest.allowed_target_ids,
        sha256=manifest.sha256,
    )
