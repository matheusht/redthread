"""Typed models for the Phase 1 autoresearch harness."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ResearchObjective(BaseModel):
    """One bounded campaign spec used by the research harness."""

    slug: str
    objective: str
    system_prompt: str
    rubric_name: str
    algorithm: str
    personas: int = 3
    depth: int | None = None
    width: int | None = None
    branching: int | None = None
    turns: int | None = None

class ResearchConfig(BaseModel):
    """Autoresearch configuration."""

    benchmark_objectives: list[ResearchObjective] = Field(default_factory=list)
    experiment_objectives: list[ResearchObjective] = Field(default_factory=list)
    lane_configs: list[ResearchLaneConfig] = Field(default_factory=list)
    control_max_average_asr: float = 0.10
    control_max_average_score: float = 2.50

class BaselineCalibration(BaseModel):
    """Baseline-derived control thresholds persisted to runtime state."""

    sample_count: int = 0
    asr_mean: float = 0.0
    asr_stdev: float = 0.0
    asr_p95: float = 0.0
    asr_max: float = 0.0
    score_mean: float = 0.0
    score_stdev: float = 0.0
    score_p95: float = 0.0
    score_max: float = 0.0
    control_max_average_asr: float = 0.0
    control_max_average_score: float = 0.0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ResearchLaneConfig(BaseModel):
    """One Phase 2 supervisor lane."""

    lane: str
    source: str
    objective_slugs: list[str] = Field(default_factory=list)

class ResearchBatchSummary(BaseModel):
    """Aggregate metrics from a research batch."""

    run_id: str
    mode: str
    lane: str | None = None
    objective_slugs: list[str]
    campaign_ids: list[str]
    total_campaigns: int
    total_results: int
    confirmed_jailbreaks: int
    near_misses: int
    average_asr: float
    average_score: float
    composite_score: float
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SupervisorCycleSummary(BaseModel):
    """Phase 2 supervisor decision over lane results."""

    run_id: str
    accepted: bool
    winning_lane: str
    rationale: str
    lane_summaries: list[ResearchBatchSummary] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ObjectiveScore(BaseModel):
    """Historical score used by the Phase 3 scheduler."""

    slug: str
    attempts: int = 0
    confirmed_jailbreaks: int = 0
    near_misses: int = 0
    average_asr: float = 0.0
    average_score: float = 0.0
    weighted_score: float = 0.0

class PhaseThreeSession(BaseModel):
    """Git-backed autoresearch session metadata."""

    tag: str
    branch: str
    base_commit: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "active"

class PhaseThreeProposal(BaseModel):
    """Supervisor proposal for accept/reject after a Phase 3 cycle."""

    proposal_id: str
    session_tag: str
    session_branch: str
    session_base_commit: str
    accepted: bool
    recommended_action: str
    rationale: str
    cycle: SupervisorCycleSummary
    runtime_config_path: str
    baseline_registry_ref: str | None = None
    checkpoint_refs: list[str] = Field(default_factory=list)
    mutation_refs: list[str] = Field(default_factory=list)
    research_memory_dir: str
    research_memory_snapshot_ref: str | None = None
    eligible_trace_ids: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BatchCheckpoint(BaseModel):
    """Partial batch execution state used for resumable research runs."""

    checkpoint_id: str
    mode: str
    lane: str | None = None
    objective_slugs: list[str] = Field(default_factory=list)
    completed_objectives: list[str] = Field(default_factory=list)
    campaign_ids: list[str] = Field(default_factory=list)
    asr_values: list[float] = Field(default_factory=list)
    score_values: list[float] = Field(default_factory=list)
    confirmed_total: int = 0
    near_miss_total: int = 0
    result_total: int = 0
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PromotionRecord(BaseModel):
    """Audit record for explicit research-to-production promotion steps."""

    promotion_id: str
    proposal_id: str
    manifest_ref: str
    validation_ref: str
    promoted_deployments: int
    promoted_trace_ids: list[str] = Field(default_factory=list)
    source_memory_dir: str
    target_memory_dir: str
    proposal_fingerprint: str
    validation_status: str = "pending"
    dry_run: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PromotionManifest(BaseModel):
    """Frozen inputs for one research-to-production promotion attempt."""

    promotion_id: str
    proposal_id: str
    session_tag: str
    source_patch_artifact: str
    baseline_registry_ref: str | None = None
    checkpoint_refs: list[str] = Field(default_factory=list)
    mutation_refs: list[str] = Field(default_factory=list)
    expected_targets: list[str] = Field(default_factory=list)
    research_memory_snapshot_ref: str | None = None
    revalidation_policy: dict[str, float | bool | str] = Field(default_factory=dict)

class PromotionValidationResult(BaseModel):
    """Result of replaying the proposal acceptance contract during promotion."""

    promotion_id: str
    proposal_id: str
    replayed_cycle: SupervisorCycleSummary
    control_gate_passed: bool
    eligible_trace_ids: list[str] = Field(default_factory=list)
    validation_status: str
    failure_reason: str | None = None

class PromotionCheckpoint(BaseModel):
    """Step-aware checkpoint for resumable promotion runs."""

    checkpoint_id: str
    promotion_id: str
    proposal_id: str
    step: str
    manifest_ref: str | None = None
    validation_ref: str | None = None
    result_ref: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
