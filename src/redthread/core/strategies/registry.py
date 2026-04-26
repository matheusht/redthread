"""Registry for RedThread attack strategy specs."""

from __future__ import annotations

import builtins
from collections.abc import Iterable

from redthread.orchestration.models import AttackStrategySpec, CostLevel, StrategyFamily


class AttackStrategyRegistry:
    """In-memory registry for RedThread-native strategy specs."""

    def __init__(self, strategies: Iterable[AttackStrategySpec] = ()) -> None:
        self._strategies: dict[str, AttackStrategySpec] = {}
        for strategy in strategies:
            self.register(strategy)

    def register(self, strategy: AttackStrategySpec, *, replace: bool = False) -> None:
        """Register a strategy, protecting against accidental duplicate ids."""
        if strategy.id in self._strategies and not replace:
            msg = f"attack strategy already registered: {strategy.id}"
            raise ValueError(msg)
        self._strategies[strategy.id] = strategy

    def get(self, strategy_id: str) -> AttackStrategySpec:
        """Return a strategy by id, or raise a clear KeyError."""
        try:
            return self._strategies[strategy_id]
        except KeyError as exc:
            msg = f"unknown attack strategy: {strategy_id}"
            raise KeyError(msg) from exc

    def list(self) -> builtins.list[AttackStrategySpec]:
        """Return strategies sorted by stable id."""
        return [self._strategies[key] for key in sorted(self._strategies)]

    def ids(self) -> builtins.list[str]:
        """Return sorted strategy ids."""
        return [strategy.id for strategy in self.list()]

    def compatible_with(self, plugin_id: str) -> builtins.list[AttackStrategySpec]:
        """Return strategies compatible with a plugin id."""
        return [strategy for strategy in self.list() if strategy.is_compatible_with(plugin_id)]

    def filter(
        self,
        *,
        family: StrategyFamily | None = None,
        max_cost: CostLevel | None = None,
        requires_multi_turn_target: bool | None = None,
    ) -> builtins.list[AttackStrategySpec]:
        """Return strategies matching supplied planning filters."""
        strategies = self.list()
        if family is not None:
            strategies = [strategy for strategy in strategies if strategy.family == family]
        if max_cost is not None:
            strategies = [s for s in strategies if _cost_rank(s.cost_level) <= _cost_rank(max_cost)]
        if requires_multi_turn_target is not None:
            strategies = [
                strategy
                for strategy in strategies
                if strategy.requires_multi_turn_target == requires_multi_turn_target
            ]
        return strategies


def _cost_rank(cost_level: CostLevel) -> int:
    return {
        CostLevel.LOW: 1,
        CostLevel.MEDIUM: 2,
        CostLevel.HIGH: 3,
    }[cost_level]
