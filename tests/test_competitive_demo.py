from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from redthread.cli import main
from redthread.reporting.competitive_demo import build_competitive_demo_artifact
from redthread.reporting.external_evidence import (
    ExternalEvidenceBundle,
    ExternalEvidenceItem,
    ExternalEvidenceSource,
)


def _weak_bundle() -> ExternalEvidenceBundle:
    return ExternalEvidenceBundle(
        source=ExternalEvidenceSource.PROMPTFOO,
        items=[
            ExternalEvidenceItem(
                source=ExternalEvidenceSource.PROMPTFOO,
                source_id="pf-1",
                title="Promptfoo weak signal",
            )
        ],
    )


def _hero_proof() -> dict[str, object]:
    return {
        "schema_version": "redthread.hero_proof.v1",
        "campaign_id": "campaign-demo",
        "metrics": {"confirmed_findings": 1, "validated_controls": 1},
        "ci_regression": {"regression_case_count": 1},
        "stages": [
            {"name": "defense_control", "status": "validated", "evidence_label": "sealed"},
            {"name": "ci_regression", "status": "ready", "evidence_label": "sealed"},
        ],
    }


def test_competitive_demo_artifact_shows_weak_to_confirmed_flow() -> None:
    artifact = build_competitive_demo_artifact(_weak_bundle(), _hero_proof())

    assert artifact["schema_version"] == "redthread.competitive_demo.v1"
    assert artifact["demo_ready"] is True
    assert [step["step"] for step in artifact["flow"]] == [
        "weak_scanner_signal",
        "redthread_confirmation",
        "validated_defense",
        "regression_artifact",
    ]
    assert artifact["flow"][0]["evidence_label"] == "imported_weak_evidence"


def test_competitive_demo_cli_writes_artifact(tmp_path: Path) -> None:
    weak_path = tmp_path / "weak.json"
    proof_path = tmp_path / "hero-proof.json"
    output = tmp_path / "demo.json"
    weak_path.write_text(_weak_bundle().model_dump_json(), encoding="utf-8")
    proof_path.write_text(json.dumps(_hero_proof()), encoding="utf-8")

    result = CliRunner().invoke(
        main,
        [
            "evidence",
            "demo",
            "--weak-evidence",
            str(weak_path),
            "--hero-proof",
            str(proof_path),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0
    assert "ready competitive demo artifact" in result.output
    assert json.loads(output.read_text())["demo_ready"] is True
