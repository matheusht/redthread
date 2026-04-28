from __future__ import annotations

import json
from pathlib import Path

from redthread.models import CampaignConfig, CampaignResult
from redthread.personas.outcomes import PersonaOutcomeRecord, PersonaOutcomeTelemetry
from redthread.reporting import (
    build_operator_artifact_bundle,
    operator_artifacts_to_markdown,
    write_campaign_report_artifacts,
)


def _telemetry_payload() -> dict[str, object]:
    telemetry = PersonaOutcomeTelemetry(
        records=[
            PersonaOutcomeRecord(
                persona_id="persona-1",
                persona_name="Plain Reporter",
                tactic="initial_access",
                technique="AML.T0054 — LLM Prompt Injection",
                algorithm="mcts",
                outcome="partial",
                weak_outcome_label="near_miss",
                judge_score=3.2,
                judge_raw_score=3,
                judge_verdict_is_jailbreak=False,
                iterations_used=2,
                duration_seconds=0.2,
                strategy_count=1,
                enabled_layers=["plain_language"],
                covered_layers=["plain_language"],
            )
        ],
        total_runs=1,
        near_misses=1,
        average_judge_score=3.2,
        enabled_layers=["plain_language"],
        covered_layers=["plain_language"],
        notes=["weak run metadata only"],
    )
    return telemetry.model_dump(mode="json")


def _campaign_with_telemetry() -> CampaignResult:
    return CampaignResult(
        config=CampaignConfig(
            objective="persona telemetry report test",
            target_system_prompt="You are a support assistant.",
        ),
        metadata={
            "runtime_mode": "sealed_dry_run",
            "persona_outcome_telemetry": _telemetry_payload(),
        },
    )


def test_operator_bundle_includes_persona_sidecar_payloads() -> None:
    bundle = build_operator_artifact_bundle(_campaign_with_telemetry())

    assert bundle.persona_outcome_telemetry["schema_version"] == (
        "redthread.persona_outcome_telemetry.v1"
    )
    assert bundle.adaptive_persona_weighting_plan["schema_version"] == (
        "redthread.adaptive_persona_weighting_plan.v1"
    )
    assert bundle.adaptive_persona_weighting_plan["ordered_layers"] == ["plain_language"]


def test_markdown_reports_persona_telemetry_as_weak_metadata() -> None:
    markdown = operator_artifacts_to_markdown(
        build_operator_artifact_bundle(_campaign_with_telemetry())
    )

    assert "## Persona Outcome Telemetry" in markdown
    assert "weak run metadata only" in markdown
    assert "JudgeAgent owns findings" in markdown
    assert "Near misses: 1" in markdown
    assert "Regression evidence: only JudgeAgent-confirmed AttackResult objects qualify" in markdown


def test_campaign_report_persists_persona_sidecars(tmp_path: Path) -> None:
    bundle = build_operator_artifact_bundle(_campaign_with_telemetry())

    manifest = write_campaign_report_artifacts(bundle, tmp_path / "reports")
    telemetry_path = Path(manifest.persona_outcome_telemetry)
    plan_path = Path(manifest.adaptive_persona_weighting_plan)
    manifest_path = Path(manifest.artifact_dir) / "manifest.json"

    assert telemetry_path.exists()
    assert plan_path.exists()
    assert json.loads(telemetry_path.read_text())["near_misses"] == 1
    assert json.loads(plan_path.read_text())["ordered_layers"] == ["plain_language"]
    manifest_data = json.loads(manifest_path.read_text())
    assert manifest_data["persona_outcome_telemetry"] == str(telemetry_path)
    assert manifest_data["adaptive_persona_weighting_plan"] == str(plan_path)


def test_campaign_report_skips_persona_sidecars_when_metadata_absent(tmp_path: Path) -> None:
    campaign = CampaignResult(
        config=CampaignConfig(objective="plain report", target_system_prompt="safe")
    )

    manifest = write_campaign_report_artifacts(
        build_operator_artifact_bundle(campaign),
        tmp_path / "reports",
    )

    assert manifest.persona_outcome_telemetry == ""
    assert manifest.adaptive_persona_weighting_plan == ""
