"""Helpers for inspecting deployment validation reports from memory."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from redthread.config.settings import RedThreadSettings
from redthread.core.defense_synthesis import DeploymentRecord
from redthread.memory.index import MemoryIndex
from redthread.research.workspace import ResearchWorkspace

MemorySource = Literal["research", "production"]


def load_validation_reports(
    settings: RedThreadSettings,
    root: Path,
    source: MemorySource,
    trace_id: str | None = None,
) -> list[DeploymentRecord]:
    """Load deployment records carrying validation reports from one memory source."""
    workspace = ResearchWorkspace(root)
    workspace.ensure_layout()
    scoped_settings = workspace.research_settings(settings) if source == "research" else settings
    index = MemoryIndex(scoped_settings)
    records = index.iter_deployments()

    if trace_id is not None:
        matched = [record for record in records if record.trace_id == trace_id]
        if not matched:
            raise LookupError(f"No deployment record found for trace_id={trace_id} in {source} memory.")
        if matched[0].validation_report is None:
            raise LookupError(
                f"Deployment record trace_id={trace_id} exists in {source} memory but has no validation report."
            )
        return matched

    reported = [record for record in records if record.validation_report is not None]
    if not reported:
        raise LookupError(f"No deployment validation reports found in {source} memory.")
    return sorted(reported, key=lambda record: record.trace_id)


def render_validation_report(record: DeploymentRecord, source: MemorySource) -> str:
    """Render one operator-facing validation report."""
    report = record.validation_report
    if report is None:
        raise ValueError("deployment record does not include a validation report")

    validation = record.validation
    replay_lines = [
        (
            f"    - {case.case_id} [{case.kind}] -> {'pass' if case.passed else 'fail'}"
            + (f" | reason: {case.failure_reason}" if case.failure_reason else "")
        )
        for case in validation.replay_cases
    ] or ["    - none"]
    failed_cases = ", ".join(report.failed_case_ids) or "none"
    exploit_cases = ", ".join(report.exploit_case_ids) or "none"
    benign_cases = ", ".join(report.benign_case_ids) or "none"
    failed_reasons = (
        "; ".join(f"{case_id}: {reason}" for case_id, reason in sorted(report.failed_case_reasons.items()))
        or "none"
    )

    return "\n".join(
        [
            f"  Trace:       {record.trace_id}",
            f"  Source:      {source}",
            f"  Target:      {record.target_model}",
            f"  Prompt hash: {record.target_system_prompt_hash}",
            f"  Category:    {record.classification.category}",
            f"  Passed:      {validation.passed}",
            f"  Mode:        {report.validation_mode}",
            f"  Evidence:    {validation.evidence_mode}",
            f"  Why:         {validation.evidence_label}",
            f"  Replay suite:{report.replay_suite_id}",
            f"  Exploit:     {exploit_cases}",
            f"  Benign:      {benign_cases}",
            f"  Failed:      {failed_cases}",
            f"  Failed why:  {failed_reasons}",
            f"  Replay cnt:  {report.replay_case_count}",
            f"  Utility cnt: {report.benign_pass_count}/{report.benign_total_count}",
            f"  Attack:      {report.blocked_attack_summary}",
            f"  Utility:     {report.benign_utility_summary}",
            f"  Clause:      {report.guardrail_clause}",
            f"  Rationale:   {report.rationale}",
            "  Replay cases:",
            *replay_lines,
        ]
    )
