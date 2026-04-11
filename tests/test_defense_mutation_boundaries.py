from __future__ import annotations

from pathlib import Path

from redthread.research.defense_mutation_boundaries import (
    ALLOWED_DEFENSE_MUTATION_FILES,
    PROTECTED_DEFENSE_MUTATION_FILES,
    PROTECTED_DEFENSE_MUTATION_PREFIXES,
    is_allowed_defense_mutation_path,
    is_protected_defense_path,
)


def test_phase6_boundary_registry_has_no_overlap() -> None:
    assert set(ALLOWED_DEFENSE_MUTATION_FILES).isdisjoint(PROTECTED_DEFENSE_MUTATION_FILES)


def test_phase6_boundary_registry_includes_replay_reporting_and_gate_surfaces(tmp_path: Path) -> None:
    blocked = [
        tmp_path / "src" / "redthread" / "core" / "defense_replay_artifacts.py",
        tmp_path / "src" / "redthread" / "core" / "defense_replay_runner.py",
        tmp_path / "src" / "redthread" / "core" / "defense_reporting_models.py",
        tmp_path / "src" / "redthread" / "core" / "defense_utility_gate.py",
        tmp_path / "src" / "redthread" / "research" / "promotion.py",
    ]
    for path in blocked:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("blocked\n", encoding="utf-8")

    assert all(is_protected_defense_path(path, tmp_path) for path in blocked)
    assert all(not is_allowed_defense_mutation_path(path, tmp_path) for path in blocked)


def test_phase6_boundary_registry_blocks_prefix_surfaces(tmp_path: Path) -> None:
    for rel in (
        "src/redthread/evaluation/judge.py",
        "src/redthread/telemetry/asi.py",
        "tests/golden_dataset/golden_traces.py",
    ):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("blocked\n", encoding="utf-8")
        assert any(rel.startswith(prefix) for prefix in PROTECTED_DEFENSE_MUTATION_PREFIXES)
        assert is_protected_defense_path(path, tmp_path)
        assert not is_allowed_defense_mutation_path(path, tmp_path)


def test_phase6_boundary_registry_allows_only_defense_assets(tmp_path: Path) -> None:
    allowed = tmp_path / "src" / "redthread" / "core" / "defense_assets.py"
    allowed.parent.mkdir(parents=True, exist_ok=True)
    allowed.write_text("allowed\n", encoding="utf-8")

    assert is_allowed_defense_mutation_path(allowed, tmp_path)
    assert not is_protected_defense_path(allowed, tmp_path)
