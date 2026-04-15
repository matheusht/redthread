"""Structured reporting models for defense validation evidence."""

from __future__ import annotations

from dataclasses import dataclass, field

from redthread.core.defense_evidence import evidence_label_for, infer_evidence_mode


@dataclass
class DefenseValidationReport:
    """Operator-facing summary of why a defense validation passed or failed."""

    trace_id: str
    replay_suite_id: str
    validation_mode: str
    evidence_mode: str = ""
    evidence_label: str = ""
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

    def __post_init__(self) -> None:
        if not self.evidence_mode:
            self.evidence_mode = infer_evidence_mode(
                self.validation_mode,
                has_replay_cases=(
                    self.replay_case_count > 0
                    or bool(self.exploit_case_ids)
                    or bool(self.benign_case_ids)
                ),
                failure_reason="",
            )
        if not self.evidence_label:
            self.evidence_label = evidence_label_for(self.evidence_mode)
