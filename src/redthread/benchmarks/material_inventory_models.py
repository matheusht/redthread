"""Prompt-safe benchmark material inventory models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BenchmarkMaterialInventoryRow(BaseModel):
    """One prompt-safe material manifest inventory row."""

    manifest_ref: str = Field(min_length=1)
    collection_id: str = Field(min_length=1)
    fixture_id: str = Field(min_length=1)
    material_ref: str = Field(min_length=1)
    material_class: str = Field(min_length=1)
    review_status: str = Field(min_length=1)
    reviewers: list[str] = Field(default_factory=list)
    reviewer_count: int = 0
    review_gate_status: str = Field(min_length=1)
    allowed_target_ids: list[str] = Field(default_factory=list)
    source_path: str = Field(min_length=1)
    source_commit: str = Field(min_length=1)
    hash_verified: bool = False
    hash_status: str = "not_checked"


class BenchmarkMaterialInventory(BaseModel):
    """Prompt-safe vault inventory payload."""

    material_root: str = Field(min_length=1)
    collection_id: str | None = None
    fixture_id: str | None = None
    material_class: str | None = None
    allowed_target_id: str | None = None
    review_gate_status: str | None = None
    limit: int | None = None
    invalid_hashes_only: bool = False
    manifest_count: int = 0
    verified_hash_count: int = 0
    invalid_hash_count: int = 0
    material_ready_count: int = 0
    material_blocked_count: int = 0
    blocked_reason_counts: dict[str, int] = Field(default_factory=dict)
    engine_decision: str = "needs_hash_check"
    operator_next_step: str = "verify hashes before replay"
    operator_summary: str = "ready=0; blocked=0; hash check needed"
    collection_counts: dict[str, int] = Field(default_factory=dict)
    material_class_counts: dict[str, int] = Field(default_factory=dict)
    hash_status_counts: dict[str, int] = Field(default_factory=dict)
    review_gate_counts: dict[str, int] = Field(default_factory=dict)
    allowed_target_counts: dict[str, int] = Field(default_factory=dict)
    manifests: list[BenchmarkMaterialInventoryRow] = Field(default_factory=list)
    raw_prompt_policy: str = "raw prompt bodies stay in the private benchmark vault and are not printed or returned"
