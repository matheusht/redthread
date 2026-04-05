"""Helpers for safe source-mutation revert checks."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from redthread.research.source_mutation_models import SourceMutationManifest


def load_manifest(path_str: str) -> SourceMutationManifest:
    """Load the manifest for a stored source-mutation candidate."""
    return SourceMutationManifest.model_validate(json.loads(Path(path_str).read_text(encoding="utf-8")))


def matches_fingerprints(root: Path, fingerprints: dict[str, str], hash_fn: Callable[[str], str]) -> bool:
    """Return True when current file hashes match the expected fingerprint map."""
    for rel_path, expected in fingerprints.items():
        path = root / rel_path
        if not path.exists():
            return False
        if hash_fn(path.read_text(encoding="utf-8")) != expected:
            return False
    return True
