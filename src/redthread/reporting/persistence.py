"""Persistence helpers for RedThread operator report artifacts."""

from __future__ import annotations

from pathlib import Path

from redthread.reporting.exporters import write_operator_artifacts
from redthread.reporting.models import OperatorArtifactBundle, OperatorReportManifest
from redthread.reporting.persona_artifacts import (
    ADAPTIVE_PERSONA_WEIGHTING_PLAN_NAME,
    PERSONA_OUTCOMES_NAME,
)
from redthread.reporting.public_artifacts import prompt_safe_json

REPORT_MARKDOWN_NAME = "operator-report.md"
REPORT_JSON_NAME = "operator-report.json"
REPORT_MANIFEST_NAME = "manifest.json"
HERO_PROOF_NAME = "hero-proof.json"
CI_REGRESSION_NAME = "ci-regression.json"


def write_campaign_report_artifacts(
    bundle: OperatorArtifactBundle,
    report_dir: Path,
    *,
    include_internal_sidecars: bool = True,
) -> OperatorReportManifest:
    """Write a standard campaign report directory and return its manifest."""
    campaign_dir = report_dir / bundle.campaign_id
    markdown_path = campaign_dir / REPORT_MARKDOWN_NAME
    json_path = campaign_dir / REPORT_JSON_NAME
    manifest_path = campaign_dir / REPORT_MANIFEST_NAME
    hero_proof_path = _write_optional_json(campaign_dir / HERO_PROOF_NAME, bundle.hero_proof)
    ci_regression_path = _write_optional_json(
        campaign_dir / CI_REGRESSION_NAME,
        bundle.ci_regression,
    )
    persona_outcomes_path = None
    weighting_plan_path = None
    if include_internal_sidecars:
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
        hero_proof=str(hero_proof_path) if hero_proof_path else "",
        ci_regression=str(ci_regression_path) if ci_regression_path else "",
        persona_outcome_telemetry=str(persona_outcomes_path) if persona_outcomes_path else "",
        adaptive_persona_weighting_plan=str(weighting_plan_path) if weighting_plan_path else "",
        evidence_labels=bundle.evidence_labels,
        bridge_prep_notes=[
            "Stable RedThread operator report artifacts are ready for future import/export mappers.",
            "External evidence must remain weak evidence until JudgeAgent confirms a finding.",
        ],
    )
    manifest_path.write_text(prompt_safe_json(manifest.model_dump(mode="json")), encoding="utf-8")
    return manifest


def _write_optional_json(path: Path, payload: dict[str, object]) -> Path | None:
    if not payload:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(prompt_safe_json(payload), encoding="utf-8")
    return path


__all__ = [
    "CI_REGRESSION_NAME",
    "HERO_PROOF_NAME",
    "REPORT_JSON_NAME",
    "REPORT_MANIFEST_NAME",
    "REPORT_MARKDOWN_NAME",
    "write_campaign_report_artifacts",
]
