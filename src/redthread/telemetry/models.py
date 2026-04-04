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
    prompt_hash: str            # SHA-256 prefix of the prompt (for consistency grouping)

    # ── Operational metrics (ARIMA targets) ──────────────────────────────────
    latency_ms: float           # End-to-end response time in milliseconds
    input_tokens: int           # Prompt token count (estimated via tiktoken)
    output_tokens: int          # Response token count (estimated via tiktoken)
    error: bool = False         # Did the call fail?
    error_type: str = ""        # "timeout" | "rate_limit" | "api_error" | ""

    # ── Semantic metrics (Consistency & Drift targets) ────────────────────────
    response_text: str          # Raw response text
    response_embedding: list[float] = Field(default_factory=list)  # Pre-computed vector
    is_canary: bool = False     # True if this was a synthetic canary prompt
    canary_id: str = ""         # Which canary prompt was used (for grouping)


class ArimaForecast(BaseModel):
    """Output from a single ARIMA anomaly check on one metric stream.

    Produced by ArimaDetector for each monitored metric.
    """

    metric_name: str            # "latency_ms" | "output_tokens" | "response_length"
    observed: float             # Actual observed value (latest in window)
    predicted: float            # ARIMA one-step-ahead forecast
    lower_bound: float          # Confidence interval lower boundary
    upper_bound: float          # Confidence interval upper boundary
    is_anomaly: bool            # observed outside [lower, upper]
    deviation_sigma: float      # Signed deviation in units of prediction std error
    n_observations: int         # Number of observations used to fit the model
    fallback_method: str = ""   # "z_score" if auto_arima unavailable (< min_obs)


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
    window_size: int            # How many records were used

    # ── Composite score ───────────────────────────────────────────────────────
    overall_score: float        # 0-100 weighted composite

    # ── Sub-scores (each 0-100) ───────────────────────────────────────────────
    response_consistency: float     # Weight 0.30 — canary embedding variance
    semantic_drift: float           # Weight 0.30 — K Core-Distance from baseline
    operational_health: float       # Weight 0.25 — ARIMA anomaly absence
    behavioral_stability: float     # Weight 0.15 — output token CV

    # ── Detail ────────────────────────────────────────────────────────────────
    anomalies: list[ArimaForecast] = Field(default_factory=list)
    is_alert: bool              # overall_score < asi_alert_threshold
    alert_threshold: float      # The threshold used (from settings)
    recommendation: str         # Human-readable health summary
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
