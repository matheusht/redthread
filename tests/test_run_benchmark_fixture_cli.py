"""Tests for using safe benchmark fixture hints in `redthread run`."""

from __future__ import annotations

from typing import Any

from click.testing import CliRunner

from redthread.cli import main
from redthread.models import CampaignConfig, CampaignResult


def test_run_cli_can_use_benchmark_fixture_metadata_context(monkeypatch: Any) -> None:
    captured: dict[str, object] = {}

    class FakeEngine:
        def __init__(self, settings: object, trace_all: bool = False) -> None:
            captured["trace_all"] = trace_all

        async def run(self, config: CampaignConfig) -> CampaignResult:
            captured["objective"] = config.objective
            captured["prompting_layer_profile"] = config.prompting_layer_profile
            return CampaignResult(config=config)

    monkeypatch.setattr("redthread.cli.run.RedThreadEngine", FakeEngine)

    result = CliRunner().invoke(
        main,
        [
            "run",
            "--objective",
            "test trusted instruction handling",
            "--system-prompt",
            "Do not reveal secrets.",
            "--benchmark-fixture",
            "spiritual-spell-0032",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    objective = str(captured["objective"])
    assert "test trusted instruction handling" in objective
    assert "Benchmark fixture context (metadata only" in objective
    assert "spiritual-spell-0032" in objective
    profile = captured["prompting_layer_profile"]
    assert isinstance(profile, dict)
    assert profile["raw_prompt_loaded"] is False
    assert "source_fixture_ids" in profile
    assert "Raw prompt bodies: not loaded" in result.output
    assert "Benchmark fixture context" in result.output


def test_run_cli_rejects_unknown_benchmark_fixture(monkeypatch: Any) -> None:
    class FakeEngine:
        def __init__(self, settings: object, trace_all: bool = False) -> None:
            raise AssertionError("engine should not start for invalid fixture")

    monkeypatch.setattr("redthread.cli.run.RedThreadEngine", FakeEngine)

    result = CliRunner().invoke(
        main,
        [
            "run",
            "--objective",
            "test trusted instruction handling",
            "--system-prompt",
            "Do not reveal secrets.",
            "--benchmark-fixture",
            "missing-fixture",
            "--dry-run",
        ],
    )

    assert result.exit_code != 0
    assert "unknown jailbreak benchmark fixture id" in result.output
