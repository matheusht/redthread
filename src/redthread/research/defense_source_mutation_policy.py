"""Allow/deny policy for bounded defense prompt mutations."""

from __future__ import annotations

from pathlib import Path

ALLOWED_DEFENSE_FILE = "src/redthread/core/defense_assets.py"
BLOCKED_DEFENSE_PREFIXES = (
    "src/redthread/evaluation/",
    "src/redthread/telemetry/",
    "tests/golden_dataset/",
)
BLOCKED_DEFENSE_FILES = {
    "src/redthread/core/defense_synthesis.py",
    "src/redthread/memory/index.py",
    "src/redthread/research/promotion.py",
    "src/redthread/research/promotion_support.py",
}


def is_allowed_defense_target(path: Path, root: Path) -> bool:
    """Return True when the file is within the bounded phase6 surface."""
    rel = path.relative_to(root).as_posix()
    if rel in BLOCKED_DEFENSE_FILES or any(rel.startswith(prefix) for prefix in BLOCKED_DEFENSE_PREFIXES):
        return False
    return rel == ALLOWED_DEFENSE_FILE


def validate_defense_touched_files(paths: list[Path], root: Path) -> bool:
    """Return True when every touched file is inside the allowed phase6 surface."""
    return bool(paths) and all(is_allowed_defense_target(path, root) for path in paths)
