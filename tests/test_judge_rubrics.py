"""Judge rubric loading and caching tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from redthread.evaluation.judge import JudgeAgent
from tests.judge_helpers import make_settings


def test_rubric_loading() -> None:
    settings = make_settings()
    with patch("redthread.pyrit_adapters.targets._build_pyrit_target"):
        judge = JudgeAgent(settings)
        rubric = judge.load_rubric("authorization_bypass")
        assert "criteria" in rubric
        assert rubric["criteria"][1]["label"] == "Full Policy Adherence"
        assert rubric["criteria"][5]["label"] == "Complete Authorization Bypass"


def test_rubric_caching() -> None:
    settings = make_settings()
    with patch("redthread.pyrit_adapters.targets._build_pyrit_target"):
        judge = JudgeAgent(settings)
        rubric1 = judge.load_rubric("authorization_bypass")
        rubric2 = judge.load_rubric("authorization_bypass")
        assert rubric1 is rubric2


def test_rubric_not_found() -> None:
    settings = make_settings()
    with patch("redthread.pyrit_adapters.targets._build_pyrit_target"):
        judge = JudgeAgent(settings)
        with pytest.raises(FileNotFoundError, match="nonexistent_rubric"):
            judge.load_rubric("nonexistent_rubric")


@pytest.mark.parametrize(
    ("name", "exp_1", "exp_5"),
    [
        ("confused_deputy", "Strict Delegation Guarding", "Complete Confused Deputy Hijack"),
        ("tool_execution_hijack", "Robust Tool Containment", "Complete Execution Hijack"),
        ("canary_exfiltration", "Zero Secret Leakage", "Complete Canary Exfiltration"),
    ],
)
def test_phase8_rubrics_loading(name: str, exp_1: str, exp_5: str) -> None:
    settings = make_settings()
    with patch("redthread.pyrit_adapters.targets._build_pyrit_target"):
        judge = JudgeAgent(settings)
        rubric = judge.load_rubric(name)
        assert rubric["rubric_name"] == name
        assert rubric["scale"]["min"] == 1
        assert rubric["scale"]["max"] == 5
        assert len(rubric["criteria"]) == 5
        assert rubric["criteria"][1]["label"] == exp_1
        assert rubric["criteria"][5]["label"] == exp_5
        assert len(rubric["evaluation_steps"]) >= 3

