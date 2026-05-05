"""Tests for prompt-safe benchmark eval CLI emit helpers."""

from __future__ import annotations

import pytest
from rich.console import Console

from redthread.cli.eval_common import emit_prompt_safe_json, emit_report


def test_emit_prompt_safe_json_rejects_target_echo() -> None:
    with pytest.raises(Exception, match="unsafe public field"):
        emit_prompt_safe_json({"cases": [{"target_echo": "unsafe echo"}]})


def test_emit_report_json_rejects_prompt_body() -> None:
    with pytest.raises(Exception, match="unsafe public field"):
        emit_report(
            Console(record=True),
            {"cases": [{"prompt_body": "unsafe prompt body"}]},
            ["safe summary"],
            as_json=True,
        )
