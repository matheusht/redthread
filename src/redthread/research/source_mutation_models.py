"""Typed models for bounded source mutation candidates."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class PatchFileArtifact(BaseModel):
    """One file payload stored inside a forward or reverse patch artifact."""

    path: str
    content: str
    sha256: str


class CandidateValidationCheck(BaseModel):
    """One additive validation check recorded alongside the base patch facts."""

    name: str
    passed: bool
    detail: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class CandidateValidationOutcome(BaseModel):
    """Structured result returned by an optional phase-specific validator."""

    passed: bool
    checks: list[CandidateValidationCheck] = Field(default_factory=list)


class PatchValidationResult(BaseModel):
    """Pre-apply validation facts for one patch candidate."""

    touched_files_allowed: bool
    reverse_patch_available: bool
    non_empty_patch: bool
    single_surface_patch: bool
    has_rationale: bool
    has_metric_goal: bool
    validator_passed: bool = True
    validator_checks: list[CandidateValidationCheck] = Field(default_factory=list)

    def all_passed(self) -> bool:
        """Return True when both base and additive validation gates passed."""
        return all(
            (
                self.touched_files_allowed,
                self.reverse_patch_available,
                self.non_empty_patch,
                self.single_surface_patch,
                self.has_rationale,
                self.has_metric_goal,
                self.validator_passed,
            )
        )


class SourceMutationManifest(BaseModel):
    """Complete provenance record for one bounded source mutation."""

    candidate_id: str
    mutation_phase: str = "phase5"
    mutation_family: str
    target_files: list[str] = Field(default_factory=list)
    touched_files: list[str] = Field(default_factory=list)
    artifact_paths: dict[str, str] = Field(default_factory=dict)
    selected_tests: list[str] = Field(default_factory=list)
    pre_apply_validation: PatchValidationResult
    before_fingerprints: dict[str, str] = Field(default_factory=dict)
    after_fingerprints: dict[str, str] = Field(default_factory=dict)


class SourceMutationCandidate(BaseModel):
    """Source of truth for one source-mutation proposal."""

    candidate_id: str = Field(default_factory=lambda: f"source-mutation-{uuid4().hex[:8]}")
    mutation_phase: str = "phase5"
    mutation_family: str
    rationale: str
    metric_goal: str
    target_files: list[str] = Field(default_factory=list)
    touched_files: list[str] = Field(default_factory=list)
    forward_patch_path: str
    reverse_patch_path: str
    patch_manifest_path: str
    reasoning_path: str
    selected_tests: list[str] = Field(default_factory=list)
    apply_status: Literal["generated", "applied", "reverted", "rejected"] = "generated"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
