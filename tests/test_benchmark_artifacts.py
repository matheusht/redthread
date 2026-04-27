"""Tests for prompt-safe benchmark artifact writers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from redthread.benchmarks.artifacts import (
    BenchmarkArtifactError,
    write_benchmark_report_artifact,
)
from redthread.benchmarks.dry_run import build_jailbreak_corpus_dry_run_report


def test_writes_prompt_safe_benchmark_report_artifact(tmp_path: Path) -> None:
    report = build_jailbreak_corpus_dry_run_report(
        fixture_ids=["spiritual-spell-0032"],
    )
    output_path = tmp_path / "reports" / "benchmark-report.json"

    result = write_benchmark_report_artifact(report, output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert result.path == str(output_path)
    assert result.schema_version == "redthread.jailbreak_benchmark_dry_run.v1"
    assert payload["selected_fixture_ids"] == ["spiritual-spell-0032"]
    assert payload["raw_prompt_policy"] == "raw prompt bodies are not loaded during dry-run"


def test_rejects_directory_output_path(tmp_path: Path) -> None:
    report = build_jailbreak_corpus_dry_run_report(limit=1)

    with pytest.raises(BenchmarkArtifactError, match="output path is a directory"):
        write_benchmark_report_artifact(report, tmp_path)
