"""Prompt-safe benchmark report artifact writers."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
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


UNSAFE_PUBLIC_KEYS = frozenset({
    "prompt",
    "prompt_body",
    "raw_prompt",
    "attacker_prompt",
    "target_echo",
    "target_response",
    "judge_reasoning",
    "reasoning",
    "raw",
})


def write_benchmark_report_artifact(
    report: BenchmarkReportPayload,
    output_path: str | Path,
) -> BenchmarkArtifactWriteResult:
    """Write a prompt-safe benchmark report JSON artifact."""
    path = Path(output_path).expanduser()
    if path.exists() and path.is_dir():
        msg = f"benchmark report output path is a directory: {output_path}"
        raise BenchmarkArtifactError(msg)
    payload = report.model_dump(mode="json")
    assert_prompt_safe_benchmark_payload(payload)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        msg = f"could not write benchmark report artifact: {output_path}"
        raise BenchmarkArtifactError(msg) from exc
    return BenchmarkArtifactWriteResult(
        path=str(path),
        schema_version=report.schema_version,
    )


def assert_prompt_safe_benchmark_payload(payload: object, path: str = "$") -> None:
    """Raise when a public benchmark artifact payload contains unsafe fields."""
    _assert_prompt_safe_payload(payload, path)


def _assert_prompt_safe_payload(payload: object, path: str = "$") -> None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            key_text = str(key)
            if key_text in UNSAFE_PUBLIC_KEYS and _has_public_value(value):
                msg = f"benchmark report contains unsafe public field: {path}.{key_text}"
                raise BenchmarkArtifactError(msg)
            _assert_prompt_safe_payload(value, f"{path}.{key_text}")
        return
    if isinstance(payload, Sequence) and not isinstance(payload, str):
        for index, item in enumerate(payload):
            _assert_prompt_safe_payload(item, f"{path}[{index}]")


def _has_public_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        stripped = value.strip()
        return bool(stripped) and not stripped.startswith("[redacted:")
    if isinstance(value, Sequence) and not isinstance(value, str):
        return bool(value)
    if isinstance(value, Mapping):
        return bool(value)
    return True
