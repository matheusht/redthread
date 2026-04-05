"""Helpers for recovering partially-applied source mutation cycles."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from redthread.research.source_mutation_models import PatchFileArtifact, SourceMutationCandidate
from redthread.research.source_mutation_revert import load_manifest, matches_fingerprints


def latest_candidate(root: Path) -> SourceMutationCandidate | None:
    """Return the latest stored source mutation candidate if one exists."""
    paths = sorted((root / "autoresearch" / "runtime" / "mutations").glob("source-mutation-*/candidate.json"))
    if not paths:
        return None
    return SourceMutationCandidate.model_validate(json.loads(paths[-1].read_text(encoding="utf-8")))


def live_state(root: Path, candidate: SourceMutationCandidate, hash_fn: Callable[[str], str]) -> str:
    """Inspect the workspace and classify the candidate's live mutation state."""
    manifest = load_manifest(candidate.patch_manifest_path)
    forward_payload = _load_patch(candidate.forward_patch_path)
    reverse_payload = _load_patch(candidate.reverse_patch_path)
    if _matches_payload(root, reverse_payload):
        return "reverted"
    if _matches_payload(root, forward_payload):
        return "applied"
    if matches_fingerprints(root, manifest.before_fingerprints, hash_fn):
        return "generated"
    if matches_fingerprints(root, manifest.after_fingerprints, hash_fn):
        return "applied"
    return "diverged"


def apply_candidate(
    root: Path,
    candidate: SourceMutationCandidate,
    hash_fn: Callable[[str], str],
) -> SourceMutationCandidate:
    """Apply a generated candidate if the workspace still matches its before-state."""
    manifest = load_manifest(candidate.patch_manifest_path)
    if not matches_fingerprints(root, manifest.before_fingerprints, hash_fn):
        raise RuntimeError("Cannot resume source mutation because the workspace no longer matches the candidate baseline.")
    for item in _load_patch(candidate.forward_patch_path):
        (root / item.path).write_text(item.content, encoding="utf-8")
    candidate.apply_status = "applied"
    Path(root / "autoresearch" / "runtime" / "mutations" / candidate.candidate_id / "candidate.json").write_text(
        candidate.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return candidate


def _matches_payload(root: Path, payload: list[PatchFileArtifact]) -> bool:
    return all((root / item.path).exists() and (root / item.path).read_text(encoding="utf-8") == item.content for item in payload)


def _load_patch(path_str: str) -> list[PatchFileArtifact]:
    payload = json.loads(Path(path_str).read_text(encoding="utf-8"))
    return [PatchFileArtifact.model_validate(item) for item in payload["files"]]
