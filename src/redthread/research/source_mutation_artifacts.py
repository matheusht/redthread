"""Patch artifact helpers for bounded source mutation work."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from redthread.research.source_mutation_models import (
    PatchFileArtifact,
    SourceMutationCandidate,
    SourceMutationManifest,
)


def load_patch(path_str: str) -> list[PatchFileArtifact]:
    """Load one stored patch payload."""
    payload = json.loads(Path(path_str).read_text(encoding="utf-8"))
    return [PatchFileArtifact.model_validate(item) for item in payload["files"]]


def apply_patch_payload(root: Path, payload: list[PatchFileArtifact]) -> None:
    """Write one patch payload into the workspace."""
    for item in payload:
        (root / item.path).write_text(item.content, encoding="utf-8")


def matches_payload(root: Path, payload: list[PatchFileArtifact]) -> bool:
    """Return True when the workspace already matches the stored payload."""
    for item in payload:
        path = root / item.path
        if not path.exists() or path.read_text(encoding="utf-8") != item.content:
            return False
    return True


def write_candidate(path: Path, candidate: SourceMutationCandidate) -> None:
    """Persist candidate metadata."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(candidate.model_dump_json(indent=2), encoding="utf-8")


def write_manifest(path: Path, manifest: SourceMutationManifest) -> None:
    """Persist manifest metadata."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")


def write_patch(path: Path, payload: list[PatchFileArtifact]) -> None:
    """Persist a forward or reverse patch payload."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"files": [item.model_dump(mode="json") for item in payload]}, indent=2),
        encoding="utf-8",
    )


def write_reasoning(path: Path, title: str, rationale: str, metric_goal: str) -> None:
    """Persist human-readable rationale for one mutation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# {title}\n\n{rationale}\n\nMetric goal: {metric_goal}\n",
        encoding="utf-8",
    )


def patch_file(root: Path, path: Path, content: str) -> PatchFileArtifact:
    """Build a file artifact for one target path."""
    return PatchFileArtifact(
        path=path.relative_to(root).as_posix(),
        content=content,
        sha256=sha256(content),
    )


def sha256(content: str) -> str:
    """Return the SHA-256 digest for one string payload."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
