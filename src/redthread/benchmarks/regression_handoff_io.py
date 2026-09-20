"""I/O and serialization helpers for prompt-safe benchmark regression handoffs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from redthread.benchmarks.artifacts import (
    BenchmarkArtifactError,
    assert_prompt_safe_benchmark_payload,
)

if TYPE_CHECKING:
    from redthread.benchmarks.regression_handoff import (
        BenchmarkRegressionHandoffArtifact,
    )


class BenchmarkRegressionHandoffError(ValueError):
    """Raised when a regression handoff artifact cannot be written or loaded."""


def write_benchmark_regression_handoff_artifact(
    artifact: BenchmarkRegressionHandoffArtifact,
    output_path: str | Path,
) -> str:
    """Write a prompt-safe benchmark regression handoff JSON artifact."""
    path = Path(output_path).expanduser()
    if path.exists() and path.is_dir():
        msg = f"benchmark regression handoff output path is a directory: {output_path}"
        raise BenchmarkRegressionHandoffError(msg)
    payload = artifact.model_dump(mode="json")
    try:
        assert_prompt_safe_benchmark_payload(payload)
    except BenchmarkArtifactError as exc:
        raise BenchmarkRegressionHandoffError(str(exc)) from exc
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        msg = f"could not write benchmark regression handoff artifact: {output_path}"
        raise BenchmarkRegressionHandoffError(msg) from exc
    return str(path)


def load_benchmark_regression_handoff_artifact(
    input_path: str | Path,
) -> dict[str, Any]:
    """Load and parse a benchmark regression handoff JSON payload."""
    path = Path(input_path).expanduser()
    if not path.is_file():
        msg = f"benchmark regression handoff artifact file not found: {input_path}"
        raise BenchmarkRegressionHandoffError(msg)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            msg = f"invalid handoff artifact format: expected JSON object at {input_path}"
            raise BenchmarkRegressionHandoffError(msg)
        return data
    except (json.JSONDecodeError, OSError) as exc:
        msg = f"could not read benchmark regression handoff artifact: {input_path}"
        raise BenchmarkRegressionHandoffError(msg) from exc
