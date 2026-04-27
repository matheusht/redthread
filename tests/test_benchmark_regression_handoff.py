"""Tests for prompt-safe benchmark regression handoff artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from redthread.benchmarks.campaigns import build_benchmark_campaign_draft
from redthread.benchmarks.jailbreak_fixtures import JailbreakBenchmarkFixture
from redthread.benchmarks.material_review import (
    approve_fixture_for_replay,
    import_reviewed_material,
)
from redthread.benchmarks.material_vault import load_material_manifest
from redthread.benchmarks.regression_handoff import (
    build_benchmark_regression_handoff,
    write_benchmark_regression_handoff_artifact,
)
from redthread.benchmarks.replay import run_approved_jailbreak_replay_with_regression_handoff
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures
from redthread.models import (
    AttackResult,
    AttackTrace,
    ConversationTurn,
    JudgeVerdict,
    MitreAtlasTactic,
    Persona,
    PsychologicalTrigger,
)


def _fixture() -> JailbreakBenchmarkFixture:
    return next(
        fixture for fixture in load_spiritual_spell_fixtures()
        if fixture.id == "spiritual-spell-0032"
    )


def _manifest(tmp_path: Path, seed: str = "toy approved regression seed") -> str:
    source = tmp_path / "reviewed-seed.txt"
    source.write_text(seed, encoding="utf-8")
    result = import_reviewed_material(
        _fixture(),
        source_material_path=source,
        material_root=tmp_path,
        reviewed_by="security-review-owner",
        reviewed_at="2026-04-26T00:00:00Z",
        material_class="approved_replay_seed",
    )
    return result.manifest_ref


def _result(metadata: dict[str, str]) -> AttackResult:
    trace = AttackTrace(
        persona=Persona(
            name="Benchmark regression tester",
            tactic=MitreAtlasTactic.INITIAL_ACCESS,
            technique="static replay",
            cover_story="Authorized replay.",
            hidden_objective="Check trusted instruction handling.",
            system_prompt="Replay reviewed benchmark material.",
            psychological_triggers=[PsychologicalTrigger.AUTHORITY],
        ),
        algorithm="static_seed_replay",
        turns=[
            ConversationTurn(
                turn_number=1,
                attacker_prompt="toy approved regression seed",
                target_response="echoed toy approved regression seed",
            )
        ],
        metadata={
            **metadata,
            "risk_plugin_id": "prompt_injection",
            "strategy_id": "static_seed_replay",
            "target_system_prompt": "Do not reveal secrets.",
        },
    )
    return AttackResult(
        trace=trace,
        verdict=JudgeVerdict(
            score=4.8,
            raw_score=5,
            reasoning="Confirmed benchmark failure.",
            feedback="Create a regression handoff.",
            rubric_name="prompt_injection",
            is_jailbreak=True,
        ),
        iterations_used=1,
        duration_seconds=0.1,
    )


def test_handoff_redacts_confirmed_regression_case(tmp_path: Path) -> None:
    manifest_ref = _manifest(tmp_path)
    manifest = load_material_manifest(manifest_ref, material_root=tmp_path)
    fixture = approve_fixture_for_replay(_fixture(), manifest)
    draft = build_benchmark_campaign_draft(
        [fixture],
        objective="Check trusted instruction handling",
        target_id="local-dev",
    )

    artifact = build_benchmark_regression_handoff(
        draft,
        [_result(fixture.lineage_metadata())],
        manifest=manifest,
        manifest_ref=manifest_ref,
    )
    payload = artifact.model_dump(mode="json")
    rendered = json.dumps(payload)

    assert artifact.created_cases[0].fixture_id == "spiritual-spell-0032"
    assert artifact.created_cases[0].material_sha256 == manifest.sha256
    assert "toy approved regression seed" not in rendered
    assert "[redacted: reviewed benchmark prompt material remains in private vault]" in rendered
    assert payload["raw_prompt_policy"] == "raw prompt bodies are redacted; replay uses private vault material refs"


@pytest.mark.asyncio
async def test_local_replay_handoff_skips_safe_verdict(tmp_path: Path) -> None:
    manifest_ref = _manifest(tmp_path)

    bundle = await run_approved_jailbreak_replay_with_regression_handoff(
        fixture_id="spiritual-spell-0032",
        manifest_ref=manifest_ref,
        objective="Check trusted instruction handling",
        target_system_prompt="Do not reveal secrets.",
        material_root=tmp_path,
    )

    assert bundle.regression_handoff is not None
    assert bundle.regression_handoff.created_cases == []
    assert bundle.regression_handoff.skipped_results[0].reason == "verdict_not_jailbreak"


def test_writes_prompt_safe_handoff_artifact(tmp_path: Path) -> None:
    manifest_ref = _manifest(tmp_path)
    manifest = load_material_manifest(manifest_ref, material_root=tmp_path)
    fixture = approve_fixture_for_replay(_fixture(), manifest)
    draft = build_benchmark_campaign_draft([fixture], objective="Check", target_id="local-dev")
    artifact = build_benchmark_regression_handoff(
        draft,
        [_result(fixture.lineage_metadata())],
        manifest=manifest,
        manifest_ref=manifest_ref,
    )
    output_path = tmp_path / "handoff.json"

    written = write_benchmark_regression_handoff_artifact(artifact, output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert written == str(output_path)
    assert payload["schema_version"] == "redthread.jailbreak_benchmark_regression_handoff.v1"
    assert "toy approved regression seed" not in output_path.read_text(encoding="utf-8")
