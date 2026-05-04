"""Benchmark evidence modes, promotion states, and scorecard contracts."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator

BENCHMARK_SCORECARD_SCHEMA_VERSION = "redthread.benchmark_scorecard.v1"
BENCHMARK_RUN_ENVELOPE_SCHEMA_VERSION = "redthread.benchmark_run_envelope.v1"
BENCHMARK_SCORE_MAX = 100.0


class BenchmarkLane(str, Enum):
    """Benchmark lanes supported by RedThread evaluation surfaces."""

    JAILBREAK = "jailbreak"
    AGENTIC_SECURITY = "agentic_security"
    CYBER_SANDBOX = "cyber_sandbox"


class BenchmarkEvidenceMode(str, Enum):
    """Evidence strength labels for benchmark artifacts."""

    METADATA_ONLY = "metadata_only"
    WEAK_IMPORTED_EVIDENCE = "weak_imported_evidence"
    SEALED_LOCAL_REPLAY = "sealed_local_replay"
    SEALED_RUNTIME_REVIEW = "sealed_runtime_review"
    JUDGE_CONFIRMED_SANDBOX = "judge_confirmed_sandbox"
    DEFENSE_VALIDATED = "defense_validated"


class BenchmarkRunMode(str, Enum):
    """Execution mode for a benchmark run."""

    DRY_RUN = "dry_run"
    SEALED_REPLAY = "sealed_replay"
    SANDBOX_REPLAY = "sandbox_replay"
    LIVE_REPLAY_DEFERRED = "live_replay_deferred"


class BenchmarkPromotionImpact(str, Enum):
    """Promotion boundary labels for benchmark evidence."""

    NONE = "none"
    HARNESS_SMOKE_ONLY = "harness_smoke_only"
    FINDING_CANDIDATE = "finding_candidate"
    REGRESSION_CANDIDATE = "regression_candidate"
    PROMOTION_REVIEW_ELIGIBLE = "promotion_review_eligible"


class BenchmarkNotScoredReason(str, Enum):
    """Reasons why a benchmark report has no composite score."""

    NORMAL_RUN_SURFACE = "normal_run_surface"
    METADATA_ONLY = "metadata_only"
    WEAK_IMPORTED_EVIDENCE = "weak_imported_evidence"
    DRY_RUN_NO_EXECUTION = "dry_run_no_execution"
    SEALED_LOCAL_SMOKE_ONLY = "sealed_local_smoke_only"
    MISSING_MANIFEST = "missing_manifest"
    UNAPPROVED_FIXTURE = "unapproved_fixture"
    NO_JUDGE_VERDICT = "no_judge_verdict"
    BLOCKED_TARGET = "blocked_target"


class BenchmarkScoreDimension(BaseModel):
    """One deterministic score dimension in a benchmark scorecard."""

    name: str = Field(min_length=1)
    points_awarded: float = Field(ge=0)
    points_possible: float = Field(gt=0)
    evidence_mode_cap: float | None = Field(default=None, ge=0)
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_points(self) -> BenchmarkScoreDimension:
        """Ensure awarded points never exceed possible points or mode caps."""
        if self.points_awarded > self.points_possible:
            msg = "points_awarded cannot exceed points_possible"
            raise ValueError(msg)
        if self.evidence_mode_cap is not None and self.points_awarded > self.evidence_mode_cap:
            msg = "points_awarded cannot exceed evidence_mode_cap"
            raise ValueError(msg)
        return self


class BenchmarkScorecard(BaseModel):
    """Deterministic benchmark scorecard payload."""

    schema_version: str = BENCHMARK_SCORECARD_SCHEMA_VERSION
    lane: BenchmarkLane
    source: str
    corpus_version: str = "unknown"
    fixture_ids: list[str] = Field(default_factory=list)
    target_id: str
    evidence_mode: BenchmarkEvidenceMode
    run_mode: BenchmarkRunMode
    promotion_impact: BenchmarkPromotionImpact
    total_score: float = Field(default=0, ge=0, le=BENCHMARK_SCORE_MAX)
    max_score: float = BENCHMARK_SCORE_MAX
    dimensions: list[BenchmarkScoreDimension] = Field(default_factory=list)
    not_scored_reason: BenchmarkNotScoredReason | None = None
    denominator: int = Field(default=0, ge=0)
    skipped_count: int = Field(default=0, ge=0)
    blocked_count: int = Field(default=0, ge=0)
    limitations: list[str] = Field(default_factory=list)

    @property
    def is_scored(self) -> bool:
        """Return whether this scorecard has a valid composite score."""
        return self.not_scored_reason is None

    @model_validator(mode="after")
    def validate_score_state(self) -> BenchmarkScorecard:
        """Keep scored and unscored states explicit."""
        if self.not_scored_reason is not None and self.total_score != 0:
            msg = "unscored benchmark scorecards must have total_score=0"
            raise ValueError(msg)
        if self.not_scored_reason is None and not self.dimensions:
            msg = "scored benchmark scorecards require dimensions"
            raise ValueError(msg)
        return self


class BenchmarkRunEnvelope(BaseModel):
    """Stable envelope for benchmark run artifacts."""

    schema_version: str = BENCHMARK_RUN_ENVELOPE_SCHEMA_VERSION
    run_id: str
    lane: BenchmarkLane
    source: str
    target_id: str
    evidence_mode: BenchmarkEvidenceMode
    artifacts: dict[str, str] = Field(default_factory=dict)
    scorecard: BenchmarkScorecard | None = None
    raw_prompt_policy: str = "raw prompt bodies are not stored in public artifacts"
    redaction_policy: str = "public artifacts redact prompts, target echoes, and judge reasoning"
