"""Regression case contracts for replaying confirmed failures."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class RegressionCase(BaseModel):
    """Durable replay target derived from a confirmed finding."""

    id: str = Field(default_factory=lambda: f"regression-{str(uuid4())[:8]}")
    source_finding_id: str = Field(min_length=1)
    risk_plugin_id: str = Field(min_length=1)
    strategy_id: str = Field(min_length=1)
    minimized_trace: dict[str, Any] = Field(default_factory=dict)
    expected_safe_behavior: str = Field(min_length=1)
    replay_schedule: str = "manual"
    severity_at_creation: str = "unknown"
