"""Registry for RedThread attack algorithm runners."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

from redthread.config.settings import AlgorithmType, RedThreadSettings
from redthread.models import AttackResult
from redthread.personas.models import Persona


class AttackStrategyRunner(Protocol):
    """Shared runner contract implemented by PAIR, TAP, Crescendo, and MCTS."""

    async def run(
        self,
        persona: Persona,
        target_system_prompt: str = "",
        rubric_name: str = "authorization_bypass",
    ) -> AttackResult: ...


AttackRunnerFactory = Callable[[RedThreadSettings], AttackStrategyRunner]


class AttackRunnerRegistry:
    """Small registry that maps algorithm keys to lazy runner factories."""

    def __init__(self) -> None:
        self._factories: dict[AlgorithmType, AttackRunnerFactory] = {}

    def register(
        self,
        algorithm: AlgorithmType,
        factory: AttackRunnerFactory,
        *,
        replace: bool = False,
    ) -> None:
        if algorithm in self._factories and not replace:
            raise ValueError(f"Attack runner already registered for algorithm '{algorithm.value}'.")
        self._factories[algorithm] = factory

    def create(self, algorithm: AlgorithmType, settings: RedThreadSettings) -> AttackStrategyRunner:
        if algorithm == AlgorithmType.AGENT_CHAIN:
            from redthread.orchestration.agents.specialized_adapter import SpecializedAttackRunner
            return SpecializedAttackRunner(settings)
        try:
            return self._factories[algorithm](settings)
        except KeyError as exc:
            available = ", ".join(self.algorithm_ids()) or "none"
            raise NotImplementedError(
                f"Algorithm '{algorithm}' not supported in AttackWorker. Available: {available}."
            ) from exc

    def algorithm_ids(self) -> Sequence[str]:
        return tuple(sorted(algorithm.value for algorithm in self._factories))


def build_default_attack_runner_registry() -> AttackRunnerRegistry:
    """Build the built-in attack runner registry with lazy imports."""
    registry = AttackRunnerRegistry()

    def pair(settings: RedThreadSettings) -> AttackStrategyRunner:
        from redthread.core.pair import PAIRAttack
        return PAIRAttack(settings)

    def tap(settings: RedThreadSettings) -> AttackStrategyRunner:
        from redthread.core.tap import TAPAttack
        return TAPAttack(settings)

    def crescendo(settings: RedThreadSettings) -> AttackStrategyRunner:
        from redthread.core.crescendo import CrescendoAttack
        return CrescendoAttack(settings)

    def mcts(settings: RedThreadSettings) -> AttackStrategyRunner:
        from redthread.core.mcts import MCTSAttack
        return MCTSAttack(settings)

    registry.register(AlgorithmType.PAIR, pair)
    registry.register(AlgorithmType.TAP, tap)
    registry.register(AlgorithmType.CRESCENDO, crescendo)
    registry.register(AlgorithmType.MCTS, mcts)
    return registry


__all__ = [
    "AttackRunnerFactory",
    "AttackRunnerRegistry",
    "AttackStrategyRunner",
    "build_default_attack_runner_registry",
]
