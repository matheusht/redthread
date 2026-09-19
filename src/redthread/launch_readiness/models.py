"""Typed launch-readiness evidence and gate models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from redthread.models import CampaignResult

Decision = Literal["ready", "conditional", "blocked"]


class LaunchReadinessConfig(BaseModel):
    """Conservative policy for the named launch-readiness preset."""

    preset_name: str = "launch-readiness"
    required_strategies: list[str] = Field(default_factory=lambda: ["pair", "tap", "crescendo"])
    require_live_judge: bool = True
    require_replay: bool = True
    require_benign_replay: bool = True
    fallback_diagnostic_only: bool = True
    max_unresolved_high_findings: int = 0

    @field_validator("required_strategies")
    @classmethod
    def validate_required_strategies(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("required_strategies must not be empty")
        if len(set(value)) != len(value):
            raise ValueError("required_strategies must be unique")
        unsupported = sorted(set(value) - {"pair", "tap", "crescendo"})
        if unsupported:
            raise ValueError(f"unsupported launch strategy: {', '.join(unsupported)}")
        return value


class StrategyReadiness(BaseModel):
    """Observed evidence for one required strategy."""

    strategy_id: str
    status: Literal["complete", "missing", "failed", "empty"]
    campaign_id: str | None = None
    run_count: int = 0
    finding_count: int = 0
    high_finding_count: int = 0
    evidence_labels: list[str] = Field(default_factory=list)
    live_judge: bool = False
    fallback_evidence: bool = False
    replay_passed: bool = False
    benign_replay_passed: bool = False
    error: str | None = None


class LaunchReplayEvidence(BaseModel):
    """Explicit baseline replay/utility proof supplied by the normal campaign path."""

    evidence_mode: str
    trace_ids: list[str] = Field(default_factory=list)
    scope_hash: str
    exploit_replay_passed: bool
    benign_passed: bool
    replay_cases: list[dict[str, Any]] = Field(default_factory=list)


class LaunchGateSummary(BaseModel):
    """Proof-based launch decision; never a universal safety certification."""

    decision: Decision
    promotable: bool = False
    gates: dict[str, bool] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)
    unresolved_high_findings: int = 0
    unknowns: list[str] = Field(default_factory=list)


class LaunchReadinessResult(BaseModel):
    """Complete launch-readiness result and prompt-safe public packet."""

    schema_version: str = "redthread.launch_readiness.v1"
    config: LaunchReadinessConfig
    strategies: list[StrategyReadiness]
    gate: LaunchGateSummary
    sanitized_packet: dict[str, Any] = Field(default_factory=dict)
    executive_markdown: str = ""


class StrategyCampaign(BaseModel):
    """Normal campaign-path output, including a captured runner failure."""

    strategy_id: str
    campaign: CampaignResult | None = None
    error: str | None = None


__all__ = [
    "Decision",
    "LaunchGateSummary",
    "LaunchReplayEvidence",
    "LaunchReadinessConfig",
    "LaunchReadinessResult",
    "StrategyCampaign",
    "StrategyReadiness",
]
