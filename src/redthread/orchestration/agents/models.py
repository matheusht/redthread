"""Typed data structures and state schemas for specialized agent nodes."""

from __future__ import annotations

from typing import Any

from typing_extensions import TypedDict


class AgentPhaseState(TypedDict, total=False):
    """State schema flowing through the specialized agent subgraphs."""

    persona_dict: dict[str, Any]
    target_system_prompt: str
    recon_findings: list[str]
    social_pretext: str
    exploit_payload: str
    turns: list[dict[str, Any]]
    current_phase: str
    is_jailbreak: bool
    metadata: dict[str, Any]
    error: str | None
    phase_errors: list[dict[str, str]]


class AgentNodeResult(TypedDict, total=False):
    """Standard output schema for an individual specialized agent node."""

    agent_name: str
    phase: str
    success: bool
    output: str
    findings: list[str]
    metadata: dict[str, Any]
