"""Competitive demo artifact from weak evidence to RedThread proof."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from redthread.reporting.external_evidence import ExternalEvidenceBundle


def build_competitive_demo_artifact(
    weak_evidence: ExternalEvidenceBundle,
    hero_proof: dict[str, Any],
) -> dict[str, Any]:
    """Show weak scanner evidence becoming RedThread-confirmed proof."""
    metrics = dict(hero_proof.get("metrics", {}))
    ci = dict(hero_proof.get("ci_regression", {}))
    stages = _stage_statuses(hero_proof)
    return {
        "schema_version": "redthread.competitive_demo.v1",
        "source": weak_evidence.source.value,
        "campaign_id": hero_proof.get("campaign_id", ""),
        "flow": [
            {
                "step": "weak_scanner_signal",
                "status": "imported_weak_only",
                "count": len(weak_evidence.items),
                "evidence_label": "imported_weak_evidence",
            },
            {
                "step": "redthread_confirmation",
                "status": "confirmed" if metrics.get("confirmed_findings", 0) else "not_confirmed",
                "count": metrics.get("confirmed_findings", 0),
                "evidence_label": "live_judge",
            },
            {
                "step": "validated_defense",
                "status": stages.get("defense_control", "not_reported"),
                "count": metrics.get("validated_controls", 0),
                "evidence_label": _stage_label(hero_proof, "defense_control"),
            },
            {
                "step": "regression_artifact",
                "status": stages.get("ci_regression", "candidate_ready"),
                "count": ci.get("regression_case_count", 0),
                "evidence_label": "sealed",
            },
        ],
        "demo_ready": _demo_ready(metrics, stages),
        "talk_track": _talk_track(metrics, weak_evidence),
        "limitations": [
            "Competitive demo is derived from artifacts; it does not execute attacks.",
            "Imported scanner rows stay weak until RedThread JudgeAgent confirms a finding.",
        ],
    }


def build_competitive_demo_from_files(
    weak_evidence_path: Path,
    hero_proof_path: Path,
) -> dict[str, Any]:
    """Load inputs and build the competitive demo artifact."""
    weak = ExternalEvidenceBundle.model_validate_json(
        weak_evidence_path.read_text(encoding="utf-8")
    )
    hero = json.loads(hero_proof_path.read_text(encoding="utf-8"))
    return build_competitive_demo_artifact(weak, hero)


def write_competitive_demo_artifact(artifact: dict[str, Any], output_path: Path) -> Path:
    """Persist the competitive demo artifact."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def _stage_statuses(hero_proof: dict[str, Any]) -> dict[str, str]:
    return {
        str(stage.get("name")): str(stage.get("status"))
        for stage in hero_proof.get("stages", [])
        if isinstance(stage, dict)
    }


def _stage_label(hero_proof: dict[str, Any], name: str) -> str:
    for stage in hero_proof.get("stages", []):
        if isinstance(stage, dict) and stage.get("name") == name:
            return str(stage.get("evidence_label", "unknown"))
    return "unknown"


def _demo_ready(metrics: dict[str, Any], stages: dict[str, str]) -> bool:
    return bool(
        metrics.get("confirmed_findings", 0)
        and metrics.get("validated_controls", 0)
        and stages.get("ci_regression") in {"ready", "candidate_ready"}
    )


def _talk_track(metrics: dict[str, Any], weak_evidence: ExternalEvidenceBundle) -> str:
    return (
        f"Imported {len(weak_evidence.items)} weak {weak_evidence.source.value} signal(s), "
        f"confirmed {metrics.get('confirmed_findings', 0)} RedThread finding(s), "
        f"and produced {metrics.get('validated_controls', 0)} validated control artifact(s)."
    )


__all__ = [
    "build_competitive_demo_artifact",
    "build_competitive_demo_from_files",
    "write_competitive_demo_artifact",
]
