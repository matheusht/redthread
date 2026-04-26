"""Built-in RedThread attack strategy catalog."""

from __future__ import annotations

from redthread.core.strategies.registry import AttackStrategyRegistry
from redthread.orchestration.models import AttackStrategySpec, CostLevel, StrategyFamily


def built_in_attack_strategies() -> list[AttackStrategySpec]:
    """Return the small Slice 1 built-in strategy catalog."""
    return [
        AttackStrategySpec(
            id="crescendo",
            name="Crescendo",
            family=StrategyFamily.MULTI_TURN,
            description="Gradual multi-turn escalation toward a policy violation.",
            compatible_plugin_ids=[
                "cross_session_data_leak",
                "prompt_injection",
                "sensitive_data_exfiltration",
                "unauthorized_action",
            ],
            cost_level=CostLevel.MEDIUM,
            max_turns=8,
            requires_multi_turn_target=True,
            supports_layering=True,
        ),
        AttackStrategySpec(
            id="gs_mcts",
            name="GS-MCTS",
            family=StrategyFamily.TREE_SEARCH,
            description="Goal-guided Monte Carlo tree search over attack branches.",
            compatible_plugin_ids=[
                "prompt_injection",
                "sensitive_data_exfiltration",
                "unauthorized_action",
                "unsafe_tool_use",
            ],
            cost_level=CostLevel.HIGH,
            max_turns=12,
            requires_multi_turn_target=True,
            supports_layering=True,
        ),
        AttackStrategySpec(
            id="pair",
            name="PAIR",
            family=StrategyFamily.MULTI_TURN,
            description="Prompt Automatic Iterative Refinement attack loop.",
            compatible_plugin_ids=[
                "sensitive_data_exfiltration",
                "system_prompt_leakage",
            ],
            cost_level=CostLevel.MEDIUM,
            max_turns=10,
            requires_multi_turn_target=True,
        ),
        AttackStrategySpec(
            id="static_seed_replay",
            name="Static seed replay",
            family=StrategyFamily.STATIC_REPLAY,
            description="Replay known seed prompts without an LLM attacker loop.",
            compatible_plugin_ids=[],
            cost_level=CostLevel.LOW,
            max_turns=1,
            uses_llm_attacker=False,
        ),
        AttackStrategySpec(
            id="tap",
            name="TAP",
            family=StrategyFamily.TREE_SEARCH,
            description="Tree of Attacks with Pruning for branching adversarial search.",
            compatible_plugin_ids=[
                "prompt_injection",
                "system_prompt_leakage",
                "unsafe_tool_use",
            ],
            cost_level=CostLevel.HIGH,
            max_turns=12,
            requires_multi_turn_target=True,
            supports_layering=True,
        ),
    ]


def default_attack_strategy_registry() -> AttackStrategyRegistry:
    """Return a registry loaded with built-in attack strategies."""
    return AttackStrategyRegistry(built_in_attack_strategies())
