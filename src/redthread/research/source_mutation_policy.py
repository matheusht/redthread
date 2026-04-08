"""Allow/deny policy for bounded source mutation work."""

from __future__ import annotations

from pathlib import Path

ALLOWED_FILES = {
    "src/redthread/personas/generator.py",
    "src/redthread/core/pair.py",
    "src/redthread/core/tap.py",
    "src/redthread/core/crescendo.py",
    "src/redthread/core/mcts.py",
}
ALLOWED_PREFIXES = ("src/redthread/research/",)
BLOCKED_PREFIXES = (
    "src/redthread/evaluation/",
    "src/redthread/core/defense_synthesis.py",
    "src/redthread/telemetry/",
    "tests/golden_dataset/",
)
BLOCKED_FILES = {
    "src/redthread/core/defense_assets.py",
    "src/redthread/memory/index.py",
    "src/redthread/research/promotion.py",
    "src/redthread/research/promotion_support.py",
}


def is_allowed_target(path: Path, root: Path) -> bool:
    """Return True when the file is within the approved mutation surface."""
    rel = path.relative_to(root).as_posix()
    if rel in BLOCKED_FILES or any(rel.startswith(prefix) for prefix in BLOCKED_PREFIXES):
        return False
    return rel in ALLOWED_FILES or any(rel.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def validate_touched_files(paths: list[Path], root: Path) -> bool:
    """Return True when every touched file is inside the approved mutation surface."""
    return bool(paths) and all(is_allowed_target(path, root) for path in paths)
