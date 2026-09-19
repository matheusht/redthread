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
