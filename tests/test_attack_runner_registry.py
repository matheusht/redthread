"""Tests for concrete attack runner registry used by AttackWorker."""

from __future__ import annotations

import pytest

from redthread.config.settings import AlgorithmType, RedThreadSettings
from redthread.core.attack_runner import AttackRunnerRegistry, build_default_attack_runner_registry


def test_default_attack_runner_registry_lists_all_builtin_algorithms() -> None:
    registry = build_default_attack_runner_registry()

    assert registry.algorithm_ids() == ("agent_chain", "crescendo", "mcts", "pair", "tap")


@pytest.mark.parametrize("algorithm", list(AlgorithmType))
def test_default_attack_runner_registry_creates_builtin_runner(algorithm: AlgorithmType) -> None:
    settings = RedThreadSettings(dry_run=True, algorithm=algorithm)
    runner = build_default_attack_runner_registry().create(algorithm, settings)

    assert hasattr(runner, "run")


def test_agent_chain_runner_can_be_overridden_in_registry() -> None:
    registry = build_default_attack_runner_registry()
    marker = object()
    registry.register(
        AlgorithmType.AGENT_CHAIN,
        lambda settings: marker,  # type: ignore[return-value]
        replace=True,
    )

    assert registry.create(AlgorithmType.AGENT_CHAIN, RedThreadSettings()) is marker


def test_attack_runner_registry_rejects_duplicate_registration() -> None:
    registry = AttackRunnerRegistry()
    registry.register(AlgorithmType.TAP, lambda settings: object())  # type: ignore[return-value]

    with pytest.raises(ValueError, match="already registered"):
        registry.register(AlgorithmType.TAP, lambda settings: object())  # type: ignore[return-value]


def test_attack_runner_registry_unknown_algorithm_error_is_clear() -> None:
    registry = AttackRunnerRegistry()
    settings = RedThreadSettings(dry_run=True)

    with pytest.raises(NotImplementedError, match="not supported"):
        registry.create(AlgorithmType.TAP, settings)
