from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from redthread.config.settings import AlgorithmType, RedThreadSettings, TargetBackend
from redthread.engine import RedThreadEngine
from redthread.models import CampaignConfig
from redthread.personas.generator import PersonaGenerator


def make_settings(tmp_path: Path) -> RedThreadSettings:
    return RedThreadSettings(
        target_backend=TargetBackend.OLLAMA,
        target_model="llama3.2:3b",
        attacker_backend=TargetBackend.OLLAMA,
        attacker_model="llama3.2:3b",
        judge_backend=TargetBackend.OPENAI,
        judge_model="gpt-4o",
        openai_api_key="test-key",
        algorithm=AlgorithmType.PAIR,
        dry_run=True,
        telemetry_enabled=True,
        log_dir=tmp_path / "logs",
        memory_dir=tmp_path / "memory",
    )


@pytest.mark.asyncio
async def test_persona_generator_dry_run_stays_offline_async(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    generator = PersonaGenerator(settings)

    with patch("redthread.pyrit_adapters.targets._build_pyrit_target", side_effect=AssertionError("must stay offline")):
        personas = await generator.generate_batch("Probe authorization bypass", count=2)

    assert len(personas) == 2
    assert all(persona.hidden_objective == "Probe authorization bypass" for persona in personas)


@pytest.mark.asyncio
async def test_engine_dry_run_stays_offline_and_labels_runtime_mode(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    engine = RedThreadEngine(settings)
    config = CampaignConfig(
        objective="Probe authorization bypass",
        target_system_prompt="You are a guarded assistant.",
        num_personas=2,
        rubric_name="authorization_bypass",
    )

    with patch("redthread.pyrit_adapters.targets._build_pyrit_target", side_effect=AssertionError("must stay offline")):
        result = await engine.run(config)

    assert result.metadata["runtime_mode"] == "sealed_dry_run"
    assert result.metadata["telemetry_mode"] == "skipped_in_dry_run"
    transcript = settings.log_dir / f"{result.id}.jsonl"
    summary = json.loads(transcript.read_text(encoding="utf-8").splitlines()[0])
    assert summary["runtime_mode"] == "sealed_dry_run"
    assert summary["telemetry_mode"] == "skipped_in_dry_run"
