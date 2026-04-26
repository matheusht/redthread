"""Weak detector signal contracts for RedThread evidence."""

from __future__ import annotations

from uuid import uuid4

from pydantic import BaseModel, Field


class DetectorHint(BaseModel):
    """Weak evidence signal that can assist, but never replace, JudgeAgent."""

    id: str = Field(default_factory=lambda: f"hint-{str(uuid4())[:8]}")
    source: str = "redthread_static"
    detector_name: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_text: str = ""
    limitations: str = "weak signal; requires JudgeAgent review"
    trace_ref: str = ""
