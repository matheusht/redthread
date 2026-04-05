"""Runtime overrides for Phase 4 prompt and setting mutations."""

from __future__ import annotations

import json
from pathlib import Path

from redthread.config.settings import RedThreadSettings


def resolve_runtime_state_path(settings: RedThreadSettings, root: Path) -> Path:
    """Resolve the mutation runtime state path for production or research runs."""
    if settings.research_runtime_dir is not None:
        return settings.research_runtime_dir / "mutation_state.json"

    runtime_path = root / "autoresearch" / "runtime" / "mutation_state.json"
    legacy_path = root / "autoresearch" / "mutation_state.json"
    if runtime_path.exists() or not legacy_path.exists():
        return runtime_path
    return legacy_path


def apply_runtime_overrides(settings: RedThreadSettings, root: Path) -> RedThreadSettings:
    """Apply autoresearch runtime overrides from disk to a settings copy."""
    overridden = settings.model_copy(deep=True)
    state_path = resolve_runtime_state_path(overridden, root)
    if not state_path.exists():
        return overridden

    data = json.loads(state_path.read_text(encoding="utf-8"))
    for field in (
        "attacker_temperature",
        "tree_depth",
        "tree_width",
        "branching_factor",
        "crescendo_max_turns",
        "crescendo_escalation_threshold",
        "mcts_simulations",
        "mcts_max_depth",
        "mcts_exploration_constant",
        "mcts_rollout_max_turns",
        "mcts_strategy_count",
        "mcts_max_budget_tokens",
    ):
        if field in data:
            setattr(overridden, field, data[field])
    return overridden
