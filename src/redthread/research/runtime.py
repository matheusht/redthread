"""Runtime overrides for Phase 4 prompt and setting mutations."""

from __future__ import annotations

import json
from pathlib import Path

from redthread.config.settings import RedThreadSettings


def apply_runtime_overrides(settings: RedThreadSettings, root: Path) -> RedThreadSettings:
    """Apply autoresearch runtime overrides from disk to a settings copy."""
    overridden = settings.model_copy(deep=True)
    state_path = root / "autoresearch" / "mutation_state.json"
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
    ):
        if field in data:
            setattr(overridden, field, data[field])
    return overridden

