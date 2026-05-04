"""Human-reviewed benchmark material import and approval helpers."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from redthread.benchmarks.jailbreak_fixtures import JailbreakBenchmarkFixture
from redthread.benchmarks.material_vault import (
    BenchmarkMaterialManifest,
    benchmark_material_root,
    safe_vault_path,
    sha256_file,
)

ReviewableMaterialClass = Literal["redacted", "approved_replay_seed"]


class MaterialReviewError(ValueError):
    """Raised when reviewed material import or approval is unsafe."""


class MaterialImportResult(BaseModel):
    """Result of copying reviewed material into the private vault."""

    manifest: BenchmarkMaterialManifest
    material_ref: str
    manifest_ref: str


def import_reviewed_material(
    fixture: JailbreakBenchmarkFixture,
    *,
    source_material_path: str | Path,
    material_root: str | Path | None = None,
    reviewed_by: str,
    reviewed_at: str,
    reviewer_ids: list[str] | None = None,
    material_class: ReviewableMaterialClass = "redacted",
    allowed_target_ids: list[str] | None = None,
    collection_id: str = "spiritual-spell",
    allow_nonlocal_targets: bool = False,
) -> MaterialImportResult:
    """Copy reviewed material into the vault and write its hash manifest."""
    root = benchmark_material_root(material_root)
    collection = _validated_collection_id(collection_id)
    targets = allowed_target_ids or ["local-dev"]
    _validate_targets(targets, allow_nonlocal_targets)
    reviewers = _reviewer_ids(reviewed_by, reviewer_ids, material_class)
    source = Path(source_material_path).expanduser().resolve()
    if not source.is_file():
        msg = f"reviewed material source file does not exist: {source_material_path}"
        raise MaterialReviewError(msg)
    material_ref = _material_ref(collection, material_class, fixture.id)
    destination = safe_vault_path(root, material_ref)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    manifest = BenchmarkMaterialManifest(
        fixture_id=fixture.id,
        material_ref=material_ref,
        sha256=sha256_file(destination),
        material_class=material_class,
        review_status=material_class,
        reviewed_by=reviewed_by,
        reviewed_at=reviewed_at,
        reviewers=reviewers,
        allowed_target_ids=targets,
        source_path=fixture.source_path,
        source_commit=fixture.source_commit,
    )
    manifest_ref = f"{collection}/manifests/{fixture.id}.json"
    manifest_path = safe_vault_path(root, manifest_ref)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest.model_dump(), indent=2) + "\n", encoding="utf-8")
    return MaterialImportResult(
        manifest=manifest,
        material_ref=material_ref,
        manifest_ref=manifest_ref,
    )


def approve_fixture_for_replay(
    fixture: JailbreakBenchmarkFixture,
    manifest: BenchmarkMaterialManifest,
) -> JailbreakBenchmarkFixture:
    """Return an executable fixture overlay after human-approved manifest review."""
    if manifest.material_class != "approved_replay_seed":
        msg = "only approved replay seed manifests can promote fixtures"
        raise MaterialReviewError(msg)
    if "local-dev" not in manifest.allowed_target_ids:
        msg = "approved replay seeds must allow local-dev replay"
        raise MaterialReviewError(msg)
    _validate_reviewer_gate(manifest.reviewers)
    _validate_manifest_matches_fixture(fixture, manifest)
    data = fixture.model_dump()
    data.update(
        {
            "prompt_material_class": "approved_replay_seed",
            "prompt_material_ref": manifest.material_ref,
            "review_status": "approved_replay_seed",
        }
    )
    return JailbreakBenchmarkFixture.model_validate(data)


def _reviewer_ids(
    reviewed_by: str,
    reviewer_ids: list[str] | None,
    material_class: ReviewableMaterialClass,
) -> list[str]:
    reviewers = {reviewed_by.strip()}
    reviewers.update(reviewer.strip() for reviewer in reviewer_ids or [] if reviewer.strip())
    if material_class == "approved_replay_seed":
        _validate_reviewer_gate(reviewers)
    return sorted(reviewers)


def _validate_reviewer_gate(reviewers: set[str] | list[str]) -> None:
    distinct_reviewers = {reviewer.strip() for reviewer in reviewers if reviewer.strip()}
    if len(distinct_reviewers) < 2:
        msg = "approved replay seeds require two distinct reviewers"
        raise MaterialReviewError(msg)


def _material_ref(collection_id: str, material_class: ReviewableMaterialClass, fixture_id: str) -> str:
    folder = "reviewed" if material_class == "approved_replay_seed" else "redacted"
    return f"{collection_id}/{folder}/{fixture_id}.txt"


def _validated_collection_id(collection_id: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", collection_id):
        msg = "collection id must be a safe slug"
        raise MaterialReviewError(msg)
    return collection_id


def _validate_targets(target_ids: list[str], allow_nonlocal_targets: bool) -> None:
    if not target_ids:
        msg = "material review requires at least one allowed target"
        raise MaterialReviewError(msg)
    if not allow_nonlocal_targets and any(target_id != "local-dev" for target_id in target_ids):
        msg = "non-local target approval requires explicit override"
        raise MaterialReviewError(msg)


def _validate_manifest_matches_fixture(
    fixture: JailbreakBenchmarkFixture,
    manifest: BenchmarkMaterialManifest,
) -> None:
    if fixture.id != manifest.fixture_id:
        msg = "manifest fixture id does not match fixture"
        raise MaterialReviewError(msg)
    if fixture.source_path != manifest.source_path:
        msg = "manifest source path does not match fixture"
        raise MaterialReviewError(msg)
    if fixture.source_commit != manifest.source_commit:
        msg = "manifest source commit does not match fixture"
        raise MaterialReviewError(msg)
