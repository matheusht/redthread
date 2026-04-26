"""Tests for RedThread attack strategy contracts and registry."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from redthread.core.strategies import AttackStrategyRegistry, default_attack_strategy_registry
from redthread.orchestration.models import AttackStrategySpec, CostLevel, StrategyFamily


def test_default_registry_lists_builtin_strategies_sorted() -> None:
    registry = default_attack_strategy_registry()

    assert registry.ids() == ["crescendo", "gs_mcts", "pair", "static_seed_replay", "tap"]


def test_prompt_injection_can_resolve_crescendo_as_valid_plan_pair() -> None:
    registry = default_attack_strategy_registry()

    compatible_ids = {strategy.id for strategy in registry.compatible_with("prompt_injection")}

    assert "crescendo" in compatible_ids
    assert registry.get("crescendo").is_compatible_with("prompt_injection")


def test_static_seed_replay_is_broadly_compatible_and_low_cost() -> None:
    registry = default_attack_strategy_registry()
    static_replay = registry.get("static_seed_replay")

    assert static_replay.is_compatible_with("unknown_future_plugin")
    assert static_replay.cost_level == CostLevel.LOW
    assert static_replay.uses_llm_attacker is False


def test_strategy_filter_by_family_cost_and_multi_turn_need() -> None:
    registry = default_attack_strategy_registry()

    tree_ids = {s.id for s in registry.filter(family=StrategyFamily.TREE_SEARCH)}
    low_or_medium_ids = {s.id for s in registry.filter(max_cost=CostLevel.MEDIUM)}
    single_turn_ids = {
        s.id for s in registry.filter(requires_multi_turn_target=False)
    }

    assert tree_ids == {"gs_mcts", "tap"}
    assert low_or_medium_ids == {"crescendo", "pair", "static_seed_replay"}
    assert single_turn_ids == {"static_seed_replay"}


def test_registry_rejects_duplicate_strategy_ids() -> None:
    strategy = AttackStrategySpec(
        id="custom_strategy",
        name="Custom strategy",
        family=StrategyFamily.SINGLE_TURN,
    )
    registry = AttackStrategyRegistry([strategy])

    with pytest.raises(ValueError, match="already registered"):
        registry.register(strategy)


def test_unknown_strategy_get_raises_clear_key_error() -> None:
    registry = default_attack_strategy_registry()

    with pytest.raises(KeyError, match="unknown attack strategy"):
        registry.get("missing")


def test_strategy_validates_max_turns() -> None:
    with pytest.raises(ValidationError):
        AttackStrategySpec(
            id="bad_strategy",
            name="Bad strategy",
            family=StrategyFamily.SINGLE_TURN,
            max_turns=0,
        )
