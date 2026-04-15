"""Structured reporting models for defense validation evidence."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DefenseValidationReport:
    """Operator-facing summary of why a defense validation passed or failed."""

    trace_id: str
    replay_suite_id: str
    validation_mode: str
    exploit_case_ids: list[str] = field(default_factory=list)
    benign_case_ids: list[str] = field(default_factory=list)
    failed_case_ids: list[str] = field(default_factory=list)
    failed_case_reasons: dict[str, str] = field(default_factory=dict)
    replay_case_count: int = 0
    benign_pass_count: int = 0
    benign_total_count: int = 0
    blocked_attack_summary: str = ""
    benign_utility_summary: str = ""
    guardrail_clause: str = ""
    rationale: str = ""
