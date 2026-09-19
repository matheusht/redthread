"""Timeout handling for LangGraph attack workers."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from redthread.config.settings import AlgorithmType, RedThreadSettings, TargetBackend
from redthread.models import MitreAtlasTactic, Persona, PsychologicalTrigger


class _SlowRunner:
    async def run(self, **_kwargs: object) -> object:
        await asyncio.sleep(0.05)
        raise AssertionError("runner should be cancelled by the worker timeout")


class _Registry:
    def create(self, _algorithm: object, _settings: object) -> _SlowRunner:
        return _SlowRunner()


def _settings() -> RedThreadSettings:
    return RedThreadSettings(
        target_backend=TargetBackend.OLLAMA,
        target_model="llama3.2:3b",
        attacker_backend=TargetBackend.OLLAMA,
        attacker_model="llama3.2:3b",
        judge_backend=TargetBackend.OPENAI,
        judge_model="gpt-4o",
        openai_api_key="test-key",
        algorithm=AlgorithmType.TAP,
        worker_timeout_seconds=0.01,
    )


def _persona() -> Persona:
    return Persona(
        name="Timeout Persona",
        tactic=MitreAtlasTactic.INITIAL_ACCESS,
        technique="AML.T0051",
        cover_story="Routine audit",
        hidden_objective="Bypass authorization checks",
        system_prompt="You are a persistent auditor.",
        psychological_triggers=[PsychologicalTrigger.AUTHORITY],
    )


@pytest.mark.asyncio
async def test_attack_worker_timeout_returns_aborted_result() -> None:
    """A stalled runner becomes a captured worker failure."""
    from redthread.orchestration.graphs.attack_graph import run_attack_worker

    settings = _settings()
    state = {
        "settings_dict": settings.model_dump(mode="json"),
        "persona_dict": _persona().model_dump(mode="json"),
        "target_system_prompt": "",
        "rubric_name": "authorization_bypass",
        "result_dict": None,
        "error": None,
    }

    with patch(
        "redthread.core.attack_runner.build_default_attack_runner_registry",
        return_value=_Registry(),
    ):
        output = await run_attack_worker(state)

    assert output["error"] == "worker_timeout"
    assert output["result_dict"] is not None
    assert output["result_dict"]["trace"]["outcome"] == "error"
    assert output["result_dict"]["trace"]["metadata"]["worker_status"] == "worker_timeout"
