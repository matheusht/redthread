"""Reviewed jailbreak benchmark material manifests and vault resolver."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, model_validator

from redthread.benchmarks.jailbreak_fixtures import JailbreakBenchmarkFixture
from redthread.benchmarks.prompt_materials import PromptMaterial, load_prompt_material

BENCHMARK_MATERIAL_ROOT_ENV = "REDTHREAD_BENCHMARK_MATERIAL_ROOT"
MATERIAL_MANIFEST_SCHEMA_VERSION = "redthread.benchmark_material_manifest.v1"
VaultMaterialClass = Literal["redacted", "approved_replay_seed"]
VaultReviewStatus = Literal["redacted", "approved_replay_seed"]


class MaterialVaultError(ValueError):
    """Raised when reviewed material manifests or vault paths are invalid."""


class BenchmarkMaterialManifest(BaseModel):
    """Hash manifest for one reviewed benchmark prompt material file."""

    schema_version: Literal["redthread.benchmark_material_manifest.v1"] = (
        "redthread.benchmark_material_manifest.v1"
    )
    fixture_id: str = Field(min_length=1)
    material_ref: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    material_class: VaultMaterialClass
    review_status: VaultReviewStatus
    reviewed_by: str = Field(min_length=1)
    reviewed_at: str = Field(min_length=1)
    reviewers: list[str] = Field(default_factory=list)
    allowed_target_ids: list[str] = Field(default_factory=lambda: ["local-dev"])
    source_path: str = Field(min_length=1)
    source_commit: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_review_gate(self) -> BenchmarkMaterialManifest:
        """Keep manifest class and review status aligned."""
        if self.material_class != self.review_status:
            msg = "material manifest class must match review status"
            raise ValueError(msg)
        if not self.reviewers:
            self.reviewers = [self.reviewed_by]
        distinct_reviewers = {reviewer.strip() for reviewer in self.reviewers if reviewer.strip()}
        distinct_reviewers.add(self.reviewed_by.strip())
        if self.material_class == "approved_replay_seed" and len(distinct_reviewers) < 2:
            msg = "approved replay seeds require two distinct reviewers"
            raise ValueError(msg)
        self.reviewers = sorted(distinct_reviewers)
        return self


def benchmark_material_root(material_root: str | Path | None = None) -> Path:
    """Resolve the benchmark material root from an argument or environment."""
    raw_root = material_root or os.environ.get(BENCHMARK_MATERIAL_ROOT_ENV)
    if raw_root is None:
        msg = f"{BENCHMARK_MATERIAL_ROOT_ENV} is required"
        raise MaterialVaultError(msg)
    root = Path(raw_root).expanduser().resolve()
    if not root.exists():
        msg = f"benchmark material root does not exist: {root}"
        raise MaterialVaultError(msg)
    return root


def load_material_manifest(
    manifest_ref: str | Path,
    *,
    material_root: str | Path | None = None,
) -> BenchmarkMaterialManifest:
    """Load a reviewed material manifest from the vault."""
    root = benchmark_material_root(material_root)
    path = safe_vault_path(root, str(manifest_ref))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        msg = f"could not read material manifest: {manifest_ref}"
        raise MaterialVaultError(msg) from exc
    except json.JSONDecodeError as exc:
        msg = f"invalid material manifest JSON: {manifest_ref}"
        raise MaterialVaultError(msg) from exc
    if not isinstance(data, Mapping):
        msg = "material manifest must contain a JSON object"
        raise MaterialVaultError(msg)
    try:
        return BenchmarkMaterialManifest.model_validate(data)
    except ValidationError as exc:
        msg = "invalid benchmark material manifest"
        raise MaterialVaultError(msg) from exc


def resolve_reviewed_material(
    fixture: JailbreakBenchmarkFixture,
    *,
    manifest_ref: str | Path,
    material_root: str | Path | None = None,
    target_id: str = "local-dev",
) -> PromptMaterial:
    """Validate a manifest and load reviewed prompt material for a fixture."""
    root = benchmark_material_root(material_root)
    manifest = load_material_manifest(manifest_ref, material_root=root)
    _validate_fixture_manifest(fixture, manifest, target_id)
    material_path = safe_vault_path(root, manifest.material_ref)
    digest = sha256_file(material_path)
    if digest != manifest.sha256:
        msg = "prompt material hash does not match manifest"
        raise MaterialVaultError(msg)
    return load_prompt_material(fixture, material_root=root)


def safe_vault_path(root: Path, ref: str) -> Path:
    """Resolve a vault-relative path and reject traversal."""
    path = (root / ref).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        msg = "vault reference escapes material root"
        raise MaterialVaultError(msg) from exc
    return path


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest for a material file."""
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        msg = f"could not hash prompt material: {path}"
        raise MaterialVaultError(msg) from exc
    return digest.hexdigest()


def _validate_fixture_manifest(
    fixture: JailbreakBenchmarkFixture,
    manifest: BenchmarkMaterialManifest,
    target_id: str,
) -> None:
    if fixture.id != manifest.fixture_id:
        msg = "material manifest fixture id does not match fixture"
        raise MaterialVaultError(msg)
    if fixture.prompt_material_ref != manifest.material_ref:
        msg = "material manifest reference does not match fixture"
        raise MaterialVaultError(msg)
    if fixture.prompt_material_class != manifest.material_class:
        msg = "material manifest class does not match fixture"
        raise MaterialVaultError(msg)
    if fixture.review_status != manifest.review_status:
        msg = "material manifest review status does not match fixture"
        raise MaterialVaultError(msg)
    if fixture.source_path != manifest.source_path:
        msg = "material manifest source path does not match fixture"
        raise MaterialVaultError(msg)
    if fixture.source_commit != manifest.source_commit:
        msg = "material manifest source commit does not match fixture"
        raise MaterialVaultError(msg)
    if fixture.is_executable and target_id not in manifest.allowed_target_ids:
        msg = "target is not allowed by material manifest"
        raise MaterialVaultError(msg)
