"""Tests for prompt-safe benchmark artifact redaction."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from redthread.benchmarks.artifacts import (
    BenchmarkArtifactError,
    write_benchmark_report_artifact,
)


class UnsafeBenchmarkReport(BaseModel):
    """Test payload that mimics a report leaking prompt material."""

    schema_version: str = "redthread.test_report.v1"
    prompt: str


class SafeBenchmarkReport(BaseModel):
    """Test payload that keeps only safe prompt policy metadata."""

    schema_version: str = "redthread.test_report.v1"
    raw_prompt_policy: str = "raw prompt bodies are not loaded"


def test_benchmark_artifact_writer_rejects_prompt_fields(tmp_path: Path) -> None:
    try:
        write_benchmark_report_artifact(
            UnsafeBenchmarkReport(prompt="raw seed must not be public"),
            tmp_path / "unsafe.json",
        )
    except BenchmarkArtifactError as exc:
        assert "unsafe public field" in str(exc)
    else:
        raise AssertionError("expected unsafe prompt field to be rejected")


def test_benchmark_artifact_writer_allows_safe_policy_text(tmp_path: Path) -> None:
    result = write_benchmark_report_artifact(
        SafeBenchmarkReport(),
        tmp_path / "safe.json",
    )

    assert result.schema_version == "redthread.test_report.v1"
    assert "raw prompt bodies are not loaded" in (tmp_path / "safe.json").read_text(
        encoding="utf-8"
    )
