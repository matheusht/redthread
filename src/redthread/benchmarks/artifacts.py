"""Prompt-safe benchmark report artifact writers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel


class BenchmarkReportPayload(Protocol):
    """Small protocol for benchmark reports that can be written as JSON."""

    schema_version: str

    def model_dump(self, *, mode: str = "python") -> dict[str, object]:
        """Return a JSON-serializable payload."""


class BenchmarkArtifactError(ValueError):
    """Raised when benchmark artifact output is invalid."""


class BenchmarkArtifactWriteResult(BaseModel):
    """Metadata for a written prompt-safe benchmark artifact."""

    path: str
    schema_version: str
    kind: str = "benchmark_report"


def write_benchmark_report_artifact(
    report: BenchmarkReportPayload,
    output_path: str | Path,
) -> BenchmarkArtifactWriteResult:
    """Write a prompt-safe benchmark report JSON artifact."""
    path = Path(output_path).expanduser()
    if path.exists() and path.is_dir():
        msg = f"benchmark report output path is a directory: {output_path}"
        raise BenchmarkArtifactError(msg)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        msg = f"could not write benchmark report artifact: {output_path}"
        raise BenchmarkArtifactError(msg) from exc
    return BenchmarkArtifactWriteResult(
        path=str(path),
        schema_version=report.schema_version,
    )
