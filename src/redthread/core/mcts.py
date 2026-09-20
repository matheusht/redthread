"""GS-MCTS — Group-aware Strategy-guided Monte Carlo Tree Search.

Implements multi-turn adversarial conversation planning via MCTS from:
  "Red-Teaming Large Language Models using Chain of Utterances" (2023)
"""

from __future__ import annotations

import logging
import random
import time
from datetime import datetime, timezone

from redthread.config.settings import RedThreadSettings
from redthread.core.mcts_helpers import (
    MCTSTree,
    derive_strategies,
    format_mcts_history,
)
from redthread.core.mcts_phases import (
    backpropagate_mcts,
    build_mcts_dry_run_result,
    compile_mcts_target_prompt,
    finalize_mcts_trace,
    resolve_mcts_system_prompt,
    select_mcts_node,
)
from redthread.core.mcts_rollout import expand_mcts_branch, simulate_mcts_rollout
from redthread.evaluation.judge import JudgeAgent
from redthread.models import AttackResult, AttackTrace, MCTSNode, Persona
from redthread.pyrit_adapters.targets import (
    RedThreadTarget,
    build_attacker,
    build_rollout_attacker,
    build_target,
)

logger = logging.getLogger(__name__)


class MCTSAttack:
    """GS-MCTS adversarial attack — strategy-guided Monte Carlo Tree Search."""

    def __init__(
        self,
        settings: RedThreadSettings,
        attacker: RedThreadTarget | None = None,
        rollout_attacker: RedThreadTarget | None = None,
        target: RedThreadTarget | None = None,
        judge: JudgeAgent | None = None,
    ) -> None:
        self.settings = settings
        self._attacker = attacker
        self._rollout_attacker = rollout_attacker
        self._target = target
        self._judge = judge or JudgeAgent(settings)
        self._tokens_consumed: int = 0

    def _get_attacker(self) -> RedThreadTarget:
        if self._attacker is None:
            self._attacker = build_attacker(self.settings)
        return self._attacker

    def _get_rollout_attacker(self) -> RedThreadTarget:
        if self._rollout_attacker is None:
            self._rollout_attacker = build_rollout_attacker(self.settings)
        return self._rollout_attacker

    def _get_target(self) -> RedThreadTarget:
        if self._target is None:
            self._target = build_target(self.settings)
        return self._target

    async def run(
        self,
        persona: Persona,
        target_system_prompt: str = "",
        rubric_name: str = "authorization_bypass",
    ) -> AttackResult:
        """Execute the full GS-MCTS loop for a given persona."""
        start_time = time.monotonic()
        self._tokens_consumed = 0
        trace = AttackTrace(
            persona=persona,
            algorithm="mcts",
            started_at=datetime.now(timezone.utc),
            metadata={"target_system_prompt": target_system_prompt} if target_system_prompt else {},
        )
        if self.settings.dry_run:
            trace.metadata["tokens_consumed"] = self._tokens_consumed
            return self._dry_run_result(trace, rubric_name, start_time)

        strategies = derive_strategies(persona, use_cop=self.settings.use_cop)
        attacker_system = resolve_mcts_system_prompt(persona, self.settings)
        root = MCTSNode(depth=0)
        tree = MCTSTree(root)
        trace.mcts_nodes.append(root)

        for sim in range(self.settings.mcts_simulations):
            if self._tokens_consumed >= self.settings.mcts_max_budget_tokens:
                logger.warning("💸 Budget exhausted (%d tokens) at sim %d", self._tokens_consumed, sim)
                break

            leaf = self._select(root, tree)
            children = await self._expand(
                leaf, tree, trace, persona, strategies, attacker_system,
                target_system_prompt, rubric_name,
            )
            if not children:
                continue

            child = children[0]
            reward = await self._simulate(child, tree, persona, target_system_prompt, rubric_name)
            child.score = reward
            self._backpropagate(child, tree, reward)

        trace.metadata["tokens_consumed"] = self._tokens_consumed
        return await self._finalize(trace, tree, rubric_name, start_time)

    def _select(self, root: MCTSNode, tree: MCTSTree) -> MCTSNode:
        return select_mcts_node(
            root, tree, self.settings.mcts_max_depth, self.settings.mcts_exploration_constant
        )

    async def _expand(
        self,
        leaf: MCTSNode,
        tree: MCTSTree,
        trace: AttackTrace | None,
        persona: Persona,
        strategies: list[str],
        attacker_system: str,
        target_system_prompt: str = "",
        rubric_name: str = "authorization_bypass",
    ) -> list[MCTSNode]:
        """Generate strategy-guided child nodes at the leaf."""
        if leaf.depth >= self.settings.mcts_max_depth:
            leaf.is_terminal = True
            return []

        history = tree.get_history(leaf)
        history_text = format_mcts_history(history)
        turn_number = leaf.depth + 1
        sampled = random.sample(strategies, min(self.settings.mcts_strategy_count, len(strategies)))
        children: list[MCTSNode] = []
        trace_id = trace.id if trace else "direct"

        for strategy in sampled:
            child, tokens = await expand_mcts_branch(
                leaf=leaf, strategy=strategy, turn_number=turn_number,
                history_text=history_text, history=history, persona=persona,
                attacker_system=attacker_system, target_system_prompt=target_system_prompt,
                attacker=self._get_attacker(), target=self._get_target(), trace_id=trace_id,
            )
            self._tokens_consumed += tokens
            tree.register(child)
            if trace:
                trace.mcts_nodes.append(child)
            children.append(child)

        leaf.is_expanded = True
        return children

    async def _simulate(
        self,
        node: MCTSNode,
        tree: MCTSTree,
        persona: Persona,
        target_system_prompt: str,
        rubric_name: str,
    ) -> float:
        """CoT rollout: simulate from node using token-constrained attacker."""
        reward, tokens = await simulate_mcts_rollout(
            node=node, tree=tree, persona=persona,
            target_system_prompt=target_system_prompt, rubric_name=rubric_name,
            rollout_attacker=self._get_rollout_attacker(), target=self._get_target(),
            judge=self._judge, max_rollout_turns=self.settings.mcts_rollout_max_turns,
            max_depth=self.settings.mcts_max_depth,
        )
        self._tokens_consumed += tokens
        return reward

    def _backpropagate(self, node: MCTSNode, tree: MCTSTree, reward: float) -> None:
        backpropagate_mcts(node, tree, reward)

    async def _finalize(
        self, trace: AttackTrace, tree: MCTSTree, rubric_name: str, start_time: float
    ) -> AttackResult:
        return await finalize_mcts_trace(trace, tree, self._judge, rubric_name, start_time)

    def _dry_run_result(self, trace: AttackTrace, rubric_name: str, start_time: float) -> AttackResult:
        return build_mcts_dry_run_result(trace, rubric_name, start_time)

    def _compile_target_prompt(
        self, history: list[tuple[str, str]], next_msg: str, target_system_prompt: str = ""
    ) -> str:
        return compile_mcts_target_prompt(history, next_msg, target_system_prompt)
