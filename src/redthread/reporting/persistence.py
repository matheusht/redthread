"""Persistence helpers for RedThread operator report artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from redthread.reporting.exporters import write_operator_artifacts
from redthread.reporting.models import OperatorArtifactBundle, OperatorReportManifest

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
    write_operator_artifacts(bundle, markdown_path=markdown_path, json_path=json_path)
    manifest = OperatorReportManifest(
        campaign_id=bundle.campaign_id,
        artifact_dir=str(campaign_dir),
        markdown_report=str(markdown_path),
        json_report=str(json_path),
        bridge_prep_notes=[
            "Stable RedThread operator report artifacts are ready for future import/export mappers.",
            "External evidence must remain weak evidence until JudgeAgent confirms a finding.",
        ],
    )
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


__all__ = [
    "REPORT_JSON_NAME",
    "REPORT_MANIFEST_NAME",
    "REPORT_MARKDOWN_NAME",
    "write_campaign_report_artifacts",
]
