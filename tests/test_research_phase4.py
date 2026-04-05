from __future__ import annotations

import json
from pathlib import Path

from redthread.research.mutations import apply_mutation, next_mutation
from redthread.research.prompt_profiles import load_prompt_profiles
from redthread.research.runtime import apply_runtime_overrides


def test_prompt_profiles_are_created_and_loaded(tmp_path: Path) -> None:
    profiles = load_prompt_profiles(tmp_path / "autoresearch" / "runtime" / "prompt_profiles.json")
    assert "pair" in profiles
    assert "tap" in profiles
    assert "crescendo" in profiles
    assert "mcts" in profiles


def test_apply_mutation_writes_profile_and_state(tmp_path: Path) -> None:
    candidate = next_mutation(tmp_path, ["prompt_injection"])
    apply_mutation(tmp_path, candidate)

    profile_path = tmp_path / "autoresearch" / "runtime" / "prompt_profiles.json"
    state_path = tmp_path / "autoresearch" / "runtime" / "mutation_state.json"

    assert profile_path.exists()
    assert state_path.exists()

    profiles = json.loads(profile_path.read_text(encoding="utf-8"))
    state = json.loads(state_path.read_text(encoding="utf-8"))

    assert "tap" in profiles
    assert "attacker_temperature" in state or "tree_width" in state


def test_runtime_overrides_apply_from_state(tmp_path: Path) -> None:
    state_path = tmp_path / "autoresearch" / "runtime" / "mutation_state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({"attacker_temperature": 0.95, "tree_depth": 7}),
        encoding="utf-8",
    )

    from redthread.config.settings import RedThreadSettings

    settings = apply_runtime_overrides(RedThreadSettings(), tmp_path)
    assert settings.attacker_temperature == 0.95
    assert settings.tree_depth == 7
