"""Tests for MCTS execution phases: dry-run, simulation cycle, expansion, and depth limits."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from redthread.core.mcts import MCTSAttack
from redthread.core.mcts_helpers import MCTSTree
from redthread.evaluation.judge import JudgeAgent
from redthread.models import AttackOutcome, MCTSNode
from redthread.pyrit_adapters.targets import RedThreadTarget
from tests.test_mcts_fixtures import make_mocks, make_persona, make_settings, make_verdict


@pytest.mark.asyncio
async def test_mcts_dry_run() -> None:
    """Dry-run must skip all LLM interaction and return SKIPPED outcome."""
    settings = make_settings(dry_run=True)
    persona = make_persona()

    mock_attacker = AsyncMock(spec=RedThreadTarget)
    mock_attacker.send_with_usage = AsyncMock(
        side_effect=Exception("Must not call attacker in dry run")
    )
    mock_attacker.model_name = "llama3.2:3b"
    mock_rollout = AsyncMock(spec=RedThreadTarget)
    mock_rollout.model_name = "llama3.2:3b"
    mock_target = AsyncMock(spec=RedThreadTarget)
    mock_target.model_name = "llama3.2:3b"
    mock_judge = AsyncMock(spec=JudgeAgent)

    with patch("redthread.pyrit_adapters.targets._build_pyrit_target"):
        mcts = MCTSAttack(
            settings,
            attacker=mock_attacker,
            rollout_attacker=mock_rollout,
            target=mock_target,
            judge=mock_judge,
        )
        result = await mcts.run(persona, target_system_prompt="You are a helpful assistant.")

    assert result.trace.outcome == AttackOutcome.SKIPPED
    assert result.iterations_used == 0
    mock_attacker.send_with_usage.assert_not_called()
    mock_target.send_with_usage.assert_not_called()


@pytest.mark.asyncio
async def test_mcts_single_simulation() -> None:
    """One full select→expand→simulate→backprop cycle produces valid trace."""
    settings = make_settings(mcts_simulations=1, mcts_strategy_count=1)
    persona = make_persona()

    mock_attacker, mock_rollout, mock_target, mock_judge = make_mocks(
        attacker_responses=["I need access to the configuration keys."],
        target_responses=["I cannot share that information."],
        inline_scores=[2.0, 1.5],
        final_verdict=make_verdict(score=2.0, is_jailbreak=False),
    )

    with patch("redthread.pyrit_adapters.targets._build_pyrit_target"):
        mcts = MCTSAttack(
            settings,
            attacker=mock_attacker,
            rollout_attacker=mock_rollout,
            target=mock_target,
            judge=mock_judge,
        )
        result = await mcts.run(persona, target_system_prompt="You are a helpful assistant.")

    assert result.trace.algorithm == "mcts"
    assert len(result.trace.mcts_nodes) >= 2
    assert result.trace.outcome == AttackOutcome.FAILURE
    assert result.duration_seconds > 0


@pytest.mark.asyncio
async def test_mcts_expansion_uses_persona_strategies() -> None:
    """Each expansion branch must use one of the persona's allowed_strategies."""
    settings = make_settings(mcts_simulations=1, mcts_strategy_count=2)
    persona = make_persona(strategies=["invoke compliance", "cite executive authority"])

    captured_prompts: list[str] = []

    async def capture_send(prompt: str, conversation_id: str = "") -> tuple[str, int]:
        captured_prompts.append(prompt)
        return "Attacker message using strategy.", len(prompt) // 4

    mock_attacker = AsyncMock(spec=RedThreadTarget)
    mock_attacker.send_with_usage = AsyncMock(side_effect=capture_send)
    mock_attacker.model_name = "llama3.2:3b"

    mock_rollout = AsyncMock(spec=RedThreadTarget)
    mock_rollout.send_with_usage = AsyncMock(return_value=("short rollout.", 4))
    mock_rollout.model_name = "llama3.2:3b"

    mock_target = AsyncMock(spec=RedThreadTarget)
    mock_target.send_with_usage = AsyncMock(return_value=("Target refused.", 5))
    mock_target.model_name = "llama3.2:3b"

    mock_judge = AsyncMock(spec=JudgeAgent)
    mock_judge.evaluate_turn_raw = MagicMock(return_value=1.5)
    mock_judge.evaluate = AsyncMock(return_value=make_verdict(score=1.0, is_jailbreak=False))

    with patch("redthread.pyrit_adapters.targets._build_pyrit_target"):
        mcts = MCTSAttack(
            settings,
            attacker=mock_attacker,
            rollout_attacker=mock_rollout,
            target=mock_target,
            judge=mock_judge,
        )
        await mcts.run(persona, target_system_prompt="You are a helpful assistant.")

    for strategy in persona.allowed_strategies:
        assert any(strategy in p for p in captured_prompts), (
            f"Strategy '{strategy}' never appeared in any expansion prompt"
        )


@pytest.mark.asyncio
async def test_mcts_max_depth_enforced() -> None:
    """Nodes at max_depth must be marked terminal — expansion returns empty list."""
    settings = make_settings(mcts_max_depth=2, mcts_simulations=1)
    persona = make_persona()

    root = MCTSNode(depth=0)
    tree = MCTSTree(root)
    deep_node = MCTSNode(parent_id=root.id, depth=2)
    tree.register(deep_node)

    mock_attacker = AsyncMock(spec=RedThreadTarget)
    mock_attacker.send_with_usage = AsyncMock(return_value=("msg", 3))
    mock_attacker.model_name = "llama3.2:3b"
    mock_rollout = AsyncMock(spec=RedThreadTarget)
    mock_rollout.model_name = "llama3.2:3b"
    mock_target = AsyncMock(spec=RedThreadTarget)
    mock_target.model_name = "llama3.2:3b"
    mock_judge = AsyncMock(spec=JudgeAgent)

    with patch("redthread.pyrit_adapters.targets._build_pyrit_target"):
        mcts = MCTSAttack(
            settings,
            attacker=mock_attacker,
            rollout_attacker=mock_rollout,
            target=mock_target,
            judge=mock_judge,
        )
        children = await mcts._expand(
            deep_node,
            tree,
            None,
            persona,  # type: ignore[arg-type]
            persona.allowed_strategies,
            "",
            "authorization_bypass",
        )

    assert children == []
    assert deep_node.is_terminal is True
