"""Filesystem exports for launch-readiness results."""

from __future__ import annotations

import json
from pathlib import Path

from .models import LaunchReadinessResult

DEFAULT_LAUNCH_REPORT_ROOT = Path("reports") / "launch-readiness"


def write_launch_readiness_reports(
    result: LaunchReadinessResult,
    *,
    report_dir: str | None = None,
    report_md: str | None = None,
    report_json: str | None = None,
) -> None:
    """Write executive Markdown and a prompt-safe summary packet."""
    directory = Path(report_dir) if report_dir else DEFAULT_LAUNCH_REPORT_ROOT
    markdown_path = Path(report_md) if report_md else directory / "launch-readiness.md"
    json_path = Path(report_json) if report_json else directory / "launch-readiness.json"
    if markdown_path:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(result.executive_markdown, encoding="utf-8")
    if json_path:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(result.sanitized_packet, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


__all__ = ["write_launch_readiness_reports"]
