"""Telemetry Data Models — Phase 5B: ARIMA & ASI.

The blood-sample schema flowing through RedThread's nervous system.

Data flow:
  TelemetryRecord (raw interaction) →
  ArimaForecast (per-metric anomaly check) →
  ASIReport (composite health verdict)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class TelemetryRecord(BaseModel):
    """A single interaction measurement — the atomic unit of Phase 5B telemetry.

    Captured for every target interaction (organic or canary) by the
    TelemetryCollector. Provides both operational and semantic signals.
    """

    id: str = Field(default_factory=lambda: f"tel-{str(uuid4())[:8]}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    target_model: str
    prompt_hash: str

    latency_ms: float
    input_tokens: int
    output_tokens: int
    error: bool = False
    error_type: str = ""

    response_text: str
    response_embedding: list[float] = Field(default_factory=list)
    is_canary: bool = False
    canary_id: str = ""


class ArimaForecast(BaseModel):
    """Output from a single ARIMA anomaly check on one metric stream.

    Produced by ArimaDetector for each monitored metric.
    """

    metric_name: str
    observed: float
    predicted: float
    lower_bound: float
    upper_bound: float
    is_anomaly: bool
    deviation_sigma: float
    n_observations: int
    fallback_method: str = ""


class ASIReport(BaseModel):
    """Agent Stability Index — the composite health verdict.

    Score interpretation:
        90-100  Excellent — no drift, fully stable
        70-89   Good — minor fluctuations, within normal range
        50-69   Warning — measurable drift, investigate
        30-49   Degraded — significant behavioral change, campaign recommended
        0-29    Critical — severe instability, immediate intervention
    """

    id: str = Field(default_factory=lambda: f"asi-{str(uuid4())[:8]}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    target_model: str
    window_size: int
    status: str = "ok"

    overall_score: float

    response_consistency: float
    semantic_drift: float
    operational_health: float
    behavioral_stability: float

    anomalies: list[ArimaForecast] = Field(default_factory=list)
    is_alert: bool
    alert_threshold: float
    recommendation: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def health_tier(self) -> str:
        """Return human-readable tier for the current score."""
        if self.overall_score >= 90:
            return "EXCELLENT"
        elif self.overall_score >= 70:
            return "GOOD"
        elif self.overall_score >= 50:
            return "WARNING"
        elif self.overall_score >= 30:
            return "DEGRADED"
        else:
            return "CRITICAL"
