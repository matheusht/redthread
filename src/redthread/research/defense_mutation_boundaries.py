"""Explicit mutable/protected surface registry for Phase 6 defense mutations."""

from __future__ import annotations

from pathlib import Path

ALLOWED_DEFENSE_MUTATION_FILES = (
    "src/redthread/core/defense_assets.py",
)

PROTECTED_DEFENSE_MUTATION_PREFIXES = (
    "src/redthread/evaluation/",
    "src/redthread/telemetry/",
    "tests/golden_dataset/",
)

PROTECTED_DEFENSE_MUTATION_FILES = (
    "src/redthread/core/defense_synthesis.py",
    "src/redthread/core/defense_replay_fixtures.py",
    "src/redthread/core/defense_replay_runner.py",
    "src/redthread/core/defense_reporting_models.py",
    "src/redthread/core/defense_utility_gate.py",
    "src/redthread/memory/index.py",
    "src/redthread/research/promotion.py",
    "src/redthread/research/promotion_support.py",
)


def relative_repo_path(path: Path, root: Path) -> str:
    """Return a stable repo-relative path for one candidate file."""
    return path.relative_to(root).as_posix()


def is_protected_defense_path(path: Path, root: Path) -> bool:
    """Return True when the file belongs to the protected Phase 6 surface."""
    rel = relative_repo_path(path, root)
    return rel in PROTECTED_DEFENSE_MUTATION_FILES or any(
        rel.startswith(prefix) for prefix in PROTECTED_DEFENSE_MUTATION_PREFIXES
    )


def is_allowed_defense_mutation_path(path: Path, root: Path) -> bool:
    """Return True when the file belongs to the mutable Phase 6 surface."""
    rel = relative_repo_path(path, root)
    return rel in ALLOWED_DEFENSE_MUTATION_FILES and not is_protected_defense_path(path, root)
