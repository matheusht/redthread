from __future__ import annotations

from redthread.config.settings import RedThreadSettings
from redthread.pyrit_adapters.client import RedThreadTarget
from redthread.pyrit_adapters.execution_records import ExecutionRecorder
from redthread.pyrit_adapters.runtime import _build_pyrit_target


def build_target(
    settings: RedThreadSettings,
    execution_recorder: ExecutionRecorder | None = None,
) -> RedThreadTarget:
    return RedThreadTarget.from_settings(
        backend=settings.target_backend,
        model=settings.target_model,
        settings=settings,
        base_url=settings.target_base_url,
        execution_recorder=execution_recorder,
    )


def build_attacker(
    settings: RedThreadSettings,
    execution_recorder: ExecutionRecorder | None = None,
) -> RedThreadTarget:
    return RedThreadTarget.from_settings(
        backend=settings.attacker_backend,
        model=settings.attacker_model,
        settings=settings,
        base_url=settings.attacker_base_url,
        execution_recorder=execution_recorder,
    )


def build_rollout_attacker(
    settings: RedThreadSettings,
    execution_recorder: ExecutionRecorder | None = None,
) -> RedThreadTarget:
    pyrit_target = _build_pyrit_target(
        backend=settings.attacker_backend,
        model=settings.attacker_model,
        base_url=settings.attacker_base_url,
        api_key=settings.openai_api_key,
        max_tokens=50,
    )
    return RedThreadTarget(
        pyrit_target=pyrit_target,
        model_name=settings.attacker_model,
        execution_recorder=execution_recorder,
    )


def build_judge_llm(
    settings: RedThreadSettings,
    execution_recorder: ExecutionRecorder | None = None,
) -> RedThreadTarget:
    return RedThreadTarget.from_settings(
        backend=settings.judge_backend,
        model=settings.judge_model,
        settings=settings,
        execution_recorder=execution_recorder,
    )


def build_defense_architect(
    settings: RedThreadSettings,
    execution_recorder: ExecutionRecorder | None = None,
) -> RedThreadTarget:
    return RedThreadTarget.from_settings(
        backend=settings.defense_architect_backend,
        model=settings.defense_architect_model,
        settings=settings,
        execution_recorder=execution_recorder,
    )
