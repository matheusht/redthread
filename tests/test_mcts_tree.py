"""Tests for MCTS tree, UCT selection, backpropagation, and strategy derivation."""

from __future__ import annotations

import pytest

from redthread.core.mcts import MCTSAttack
from redthread.core.mcts_helpers import (
    TRIGGER_STRATEGY_MAP,
    MCTSTree,
    derive_strategies,
)
from redthread.models import MCTSNode, PsychologicalTrigger
from tests.test_mcts_fixtures import make_persona, make_settings


@pytest.mark.asyncio
async def test_mcts_uct_selection() -> None:
    """UCT should prefer high-reward nodes (exploitation) over low-visit nodes."""
    tree = MCTSTree(MCTSNode(depth=0))

    high_reward = MCTSNode(parent_id=tree.root.id, depth=1, visit_count=5, total_reward=20.0)
    low_reward = MCTSNode(parent_id=tree.root.id, depth=1, visit_count=5, total_reward=5.0)
    tree.register(high_reward)
    tree.register(low_reward)
    tree.root.visit_count = 10

    uct_high = tree.uct_score(high_reward, tree.root.visit_count, c=1.41)
    uct_low = tree.uct_score(low_reward, tree.root.visit_count, c=1.41)

    assert uct_high > uct_low


def test_mcts_unvisited_priority() -> None:
    """Unvisited nodes must receive inf UCT score — always explored first."""
    tree = MCTSTree(MCTSNode(depth=0))
    unvisited = MCTSNode(parent_id=tree.root.id, depth=1, visit_count=0)
    visited = MCTSNode(parent_id=tree.root.id, depth=1, visit_count=10, total_reward=8.0)
    tree.register(unvisited)
    tree.register(visited)

    uct_unvisited = tree.uct_score(unvisited, parent_visits=10, c=1.41)
    uct_visited = tree.uct_score(visited, parent_visits=10, c=1.41)

    assert uct_unvisited == float("inf")
    assert uct_unvisited > uct_visited


def test_mcts_backpropagation() -> None:
    """Reward must be propagated to all ancestors including root."""
    root = MCTSNode(depth=0)
    tree = MCTSTree(root)

    child = MCTSNode(parent_id=root.id, depth=1)
    grandchild = MCTSNode(parent_id=child.id, depth=2)
    tree.register(child)
    tree.register(grandchild)

    settings = make_settings()
    mcts = MCTSAttack.__new__(MCTSAttack)
    mcts.settings = settings
    mcts._tokens_consumed = 0

    mcts._backpropagate(grandchild, tree, reward=4.0)

    assert grandchild.visit_count == 1
    assert grandchild.total_reward == 4.0
    assert child.visit_count == 1
    assert child.total_reward == 4.0
    assert root.visit_count == 1
    assert root.total_reward == 4.0


def test_mcts_tree_path_reconstruction() -> None:
    """MCTSTree.get_history() must return correct (attacker, target) pairs in order."""
    root = MCTSNode(depth=0)
    tree = MCTSTree(root)

    child = MCTSNode(
        parent_id=root.id,
        depth=1,
        attacker_prompt="Hello, I am requesting access.",
        target_response="Please verify your identity.",
    )
    grandchild = MCTSNode(
        parent_id=child.id,
        depth=2,
        attacker_prompt="I am the compliance director.",
        target_response="I cannot share that without authorization.",
    )
    tree.register(child)
    tree.register(grandchild)

    history = tree.get_history(grandchild)

    assert len(history) == 2
    assert history[0] == (child.attacker_prompt, child.target_response)
    assert history[1] == (grandchild.attacker_prompt, grandchild.target_response)


def test_derive_strategies_uses_persona_list() -> None:
    """derive_strategies must prefer persona.allowed_strategies when non-empty."""
    persona = make_persona(strategies=["custom strategy A", "custom strategy B"])
    strategies = derive_strategies(persona)
    assert strategies == ["custom strategy A", "custom strategy B"]


def test_derive_strategies_fallback_from_triggers() -> None:
    """derive_strategies must derive from triggers when allowed_strategies is empty."""
    persona = make_persona(strategies=[])
    strategies = derive_strategies(persona)
    assert len(strategies) > 0
    expected_pool = (
        TRIGGER_STRATEGY_MAP[PsychologicalTrigger.AUTHORITY.value]
        + TRIGGER_STRATEGY_MAP[PsychologicalTrigger.URGENCY.value]
    )
    assert all(s in expected_pool for s in strategies)
