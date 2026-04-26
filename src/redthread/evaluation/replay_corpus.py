"""Replay corpus models for agentic-security promotion gates."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReplayTrace(BaseModel):
    trace_id: str
    threat: str
    scenario_result: dict[str, object] = Field(default_factory=dict)
    authorization_decision: dict[str, object] | None = None
    canary_report: dict[str, object] = Field(default_factory=dict)
    budget_decision: dict[str, object] = Field(default_factory=dict)
    expected_authorization: str | None = None
    expect_canary_contained: bool | None = None
    expect_budget_stop: bool | None = None


class ReplayBundle(BaseModel):
    bundle_id: str
    bridge_workflow_context: dict[str, object] = Field(default_factory=dict)
    traces: list[ReplayTrace] = Field(default_factory=list)
