"""Typed models for resumable research daemon state."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

DaemonStatusValue = Literal[
    "idle",
    "running",
    "awaiting_review",
    "cooldown",
    "halted",
    "stop_requested",
    "stopped",
]
ResearchStep = Literal[
    "idle",
    "baseline_completed",
    "lane_pack_completed",
    "mutation_candidate_generated",
    "mutation_applied",
    "proposal_emitted",
    "promotion_validation_completed",
    "promotion_completed",
]


class ResearchSessionLock(BaseModel):
    """Exclusive ownership record for one research workspace."""

    owner_id: str
    session_tag: str
    branch: str
    pid: int
    acquired_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResearchHeartbeat(BaseModel):
    """Periodic heartbeat used to detect stale daemon sessions."""

    owner_id: str
    session_tag: str
    step: ResearchStep
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResearchDaemonState(BaseModel):
    """Persistent daemon state for resumable research execution."""

    owner_id: str
    session_tag: str
    branch: str
    status: DaemonStatusValue = "idle"
    current_step: ResearchStep = "idle"
    last_completed_step: ResearchStep = "idle"
    consecutive_failures: int = 0
    cooldown_until: datetime | None = None
    last_error: str | None = None
    latest_candidate_id: str | None = None
    latest_proposal_id: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResearchFailureEntry(BaseModel):
    """Append-only daemon failure or recovery event."""

    owner_id: str
    session_tag: str
    step: ResearchStep
    severity: Literal["info", "warning", "error"]
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResearchDaemonStatus(BaseModel):
    """Human-readable snapshot returned by daemon status commands."""

    session_tag: str | None = None
    branch: str | None = None
    active_lock: bool = False
    stale_lock: bool = False
    last_heartbeat_at: datetime | None = None
    current_step: ResearchStep = "idle"
    status: DaemonStatusValue = "idle"
    consecutive_failures: int = 0
    cooldown_until: datetime | None = None
    latest_candidate_id: str | None = None
    latest_proposal_id: str | None = None
