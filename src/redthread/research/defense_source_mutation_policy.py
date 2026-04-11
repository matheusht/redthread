"""Allow/deny policy for bounded defense prompt mutations."""

from __future__ import annotations

from pathlib import Path

from redthread.research.defense_mutation_boundaries import is_allowed_defense_mutation_path


def is_allowed_defense_target(path: Path, root: Path) -> bool:
    """Return True when the file is within the bounded phase6 surface."""
    return is_allowed_defense_mutation_path(path, root)


def validate_defense_touched_files(paths: list[Path], root: Path) -> bool:
    """Return True when every touched file is inside the allowed phase6 surface."""
    return bool(paths) and all(is_allowed_defense_target(path, root) for path in paths)
