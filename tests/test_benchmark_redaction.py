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


class UnsafeNestedBenchmarkReport(BaseModel):
    """Test payload that mimics nested public artifact leaks."""

    schema_version: str = "redthread.test_report.v1"
    cases: list[dict[str, str]]


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


def test_benchmark_artifact_writer_rejects_nested_target_echo(tmp_path: Path) -> None:
    try:
        write_benchmark_report_artifact(
            UnsafeNestedBenchmarkReport(cases=[{"target_echo": "unsafe target echo"}]),
            tmp_path / "unsafe-target-echo.json",
        )
    except BenchmarkArtifactError as exc:
        assert "$.cases[0].target_echo" in str(exc)
    else:
        raise AssertionError("expected unsafe target echo field to be rejected")


def test_benchmark_artifact_writer_rejects_nested_judge_reasoning(tmp_path: Path) -> None:
    try:
        write_benchmark_report_artifact(
            UnsafeNestedBenchmarkReport(cases=[{"judge_reasoning": "unsafe judge chain"}]),
            tmp_path / "unsafe-judge-reasoning.json",
        )
    except BenchmarkArtifactError as exc:
        assert "$.cases[0].judge_reasoning" in str(exc)
    else:
        raise AssertionError("expected unsafe judge reasoning field to be rejected")


def test_benchmark_artifact_writer_rejects_nested_prompt_body(tmp_path: Path) -> None:
    try:
        write_benchmark_report_artifact(
            UnsafeNestedBenchmarkReport(cases=[{"prompt_body": "unsafe prompt body"}]),
            tmp_path / "unsafe-prompt-body.json",
        )
    except BenchmarkArtifactError as exc:
        assert "$.cases[0].prompt_body" in str(exc)
    else:
        raise AssertionError("expected unsafe prompt body field to be rejected")


def test_benchmark_artifact_writer_allows_safe_policy_text(tmp_path: Path) -> None:
    result = write_benchmark_report_artifact(
        SafeBenchmarkReport(),
        tmp_path / "safe.json",
    )

    assert result.schema_version == "redthread.test_report.v1"
    assert "raw prompt bodies are not loaded" in (tmp_path / "safe.json").read_text(
        encoding="utf-8"
    )
