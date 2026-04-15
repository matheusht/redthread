"""Helpers for inspecting promotion results with replay-case detail."""

from __future__ import annotations

import json
from pathlib import Path

from redthread.config.settings import RedThreadSettings
from redthread.memory.index import MemoryIndex
from redthread.research.workspace import ResearchWorkspace


def render_latest_promotion(settings: RedThreadSettings, root: Path) -> str:
    """Render the latest promotion result with trace-level replay detail."""
    workspace = ResearchWorkspace(root)
    workspace.ensure_layout()
    results = sorted(workspace.promotions_dir.glob("*/promotion_result.json"), key=lambda path: path.stat().st_mtime)
    if not results:
        raise LookupError("No promotion results found.")

    result_payload = json.loads(results[-1].read_text(encoding="utf-8"))
    validation_payload = json.loads(Path(result_payload["validation_ref"]).read_text(encoding="utf-8"))
    weak_records = validation_payload.get("validation_failures_by_trace", {})
    coverage = validation_payload.get("defense_report_coverage", {})
    lines = [
        f"  Promotion: {result_payload['promotion_id']}",
        f"  Proposal:  {result_payload['proposal_id']}",
        f"  Status:    {result_payload['validation_status']}",
        f"  Reports:   {len(result_payload.get('defense_report_refs', []))}",
        f"  Eligible:  {', '.join(validation_payload.get('eligible_trace_ids', [])) or 'none'}",
        f"  Coverage:  {', '.join(f'{trace}={state}' for trace, state in sorted(coverage.items())) or 'none'}",
    ]
    if validation_payload.get("failure_reason"):
        lines.append(f"  Failure:   {validation_payload['failure_reason']}")
    if validation_payload.get("missing_report_trace_ids"):
        lines.append(f"  Missing:   {', '.join(validation_payload['missing_report_trace_ids'])}")
    if validation_payload.get("weak_evidence_trace_ids"):
        lines.append(f"  Weak:      {', '.join(validation_payload['weak_evidence_trace_ids'])}")
    if validation_payload.get("failed_validation_trace_ids"):
        lines.append(f"  Failed:    {', '.join(validation_payload['failed_validation_trace_ids'])}")
    if weak_records:
        rendered = '; '.join(f"{trace_id} -> {', '.join(failures)}" for trace_id, failures in sorted(weak_records.items()))
        lines.append(f"  Fail map:  {rendered}")

    trace_details = _render_trace_details(settings, workspace, validation_payload)
    if trace_details:
        lines.extend(["  Trace detail:", *trace_details])
    return "\n".join(lines)


def _render_trace_details(
    settings: RedThreadSettings,
    workspace: ResearchWorkspace,
    validation_payload: dict[str, object],
) -> list[str]:
    trace_ids = _failing_trace_ids(validation_payload)
    if not trace_ids:
        return []

    records = {
        record.trace_id: record
        for record in MemoryIndex(workspace.research_settings(settings)).iter_deployments()
        if record.trace_id in trace_ids
    }
    lines: list[str] = []
    for trace_id in trace_ids:
        record = records.get(trace_id)
        if record is None:
            lines.append(f"    - {trace_id}: no research deployment record found")
            continue
        if record.validation_report is None:
            lines.append(f"    - {trace_id}: validation report missing")
            continue
        case_failures = [
            f"{case.case_id} ({case.kind}) -> {case.failure_reason or 'failed without explicit reason'}"
            for case in record.validation.replay_cases
            if not case.passed
        ]
        if not case_failures:
            case_failures = ["no replay-case failure recorded"]
        lines.append(
            "    - "
            f"{trace_id}: evidence={record.validation.evidence_mode}; "
            f"passed={record.validation.passed}; "
            f"failed_cases={', '.join(record.validation_report.failed_case_ids) or 'none'}"
        )
        for failure in case_failures:
            lines.append(f"      * {failure}")
    return lines


def _failing_trace_ids(validation_payload: dict[str, object]) -> list[str]:
    ordered: list[str] = []
    for key in (
        "missing_report_trace_ids",
        "weak_evidence_trace_ids",
        "failed_validation_trace_ids",
    ):
        trace_ids = validation_payload.get(key, [])
        if isinstance(trace_ids, list):
            for trace_id in trace_ids:
                if isinstance(trace_id, str) and trace_id not in ordered:
                    ordered.append(trace_id)
    failure_map = validation_payload.get("validation_failures_by_trace", {})
    if isinstance(failure_map, dict):
        for trace_id in failure_map:
            if isinstance(trace_id, str) and trace_id not in ordered:
                ordered.append(trace_id)
    return ordered


__all__ = ["render_latest_promotion"]
