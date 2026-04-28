"""Persistence helpers for RedThread operator report artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from redthread.reporting.exporters import write_operator_artifacts
from redthread.reporting.models import OperatorArtifactBundle, OperatorReportManifest
from redthread.reporting.persona_artifacts import (
    ADAPTIVE_PERSONA_WEIGHTING_PLAN_NAME,
    PERSONA_OUTCOMES_NAME,
)

REPORT_MARKDOWN_NAME = "operator-report.md"
REPORT_JSON_NAME = "operator-report.json"
REPORT_MANIFEST_NAME = "manifest.json"


def write_campaign_report_artifacts(
    bundle: OperatorArtifactBundle,
    report_dir: Path,
) -> OperatorReportManifest:
    """Write a standard campaign report directory and return its manifest."""
    campaign_dir = report_dir / bundle.campaign_id
    markdown_path = campaign_dir / REPORT_MARKDOWN_NAME
    json_path = campaign_dir / REPORT_JSON_NAME
    manifest_path = campaign_dir / REPORT_MANIFEST_NAME
    persona_outcomes_path = _write_optional_json(
        campaign_dir / PERSONA_OUTCOMES_NAME,
        bundle.persona_outcome_telemetry,
    )
    weighting_plan_path = _write_optional_json(
        campaign_dir / ADAPTIVE_PERSONA_WEIGHTING_PLAN_NAME,
        bundle.adaptive_persona_weighting_plan,
    )
    write_operator_artifacts(bundle, markdown_path=markdown_path, json_path=json_path)
    manifest = OperatorReportManifest(
        campaign_id=bundle.campaign_id,
        artifact_dir=str(campaign_dir),
        markdown_report=str(markdown_path),
        json_report=str(json_path),
        persona_outcome_telemetry=str(persona_outcomes_path) if persona_outcomes_path else "",
        adaptive_persona_weighting_plan=str(weighting_plan_path) if weighting_plan_path else "",
        bridge_prep_notes=[
            "Stable RedThread operator report artifacts are ready for future import/export mappers.",
            "External evidence must remain weak evidence until JudgeAgent confirms a finding.",
        ],
    )
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _write_optional_json(path: Path, payload: dict[str, object]) -> Path | None:
    if not payload:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


__all__ = [
    "REPORT_JSON_NAME",
    "REPORT_MANIFEST_NAME",
    "REPORT_MARKDOWN_NAME",
    "write_campaign_report_artifacts",
]
