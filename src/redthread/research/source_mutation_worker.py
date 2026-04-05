"""Template-driven bounded source mutation worker."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from redthread.research.source_mutation_models import (
    PatchFileArtifact,
    PatchValidationResult,
    SourceMutationCandidate,
    SourceMutationManifest,
)
from redthread.research.source_mutation_policy import validate_touched_files
from redthread.research.source_mutation_registry import TEMPLATES, SourceMutationTemplate
from redthread.research.source_mutation_revert import load_manifest, matches_fingerprints
from redthread.research.workspace import ResearchWorkspace


class SourceMutationWorker:
    """Generate, validate, apply, inspect, and revert bounded source mutations."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.workspace = ResearchWorkspace(root)
        self.workspace.ensure_layout()

    def generate_and_apply(self, ranked_slugs: list[str]) -> SourceMutationCandidate:
        """Create one candidate, persist all artifacts, then apply it."""
        candidate, manifest, forward_payload = self._build_candidate(ranked_slugs)
        self._write_candidate(candidate)
        self._write_manifest(manifest)
        self._apply_patch_payload(forward_payload)
        candidate.apply_status = "applied"
        self._write_candidate(candidate)
        return candidate

    def latest_candidate(self) -> SourceMutationCandidate:
        """Load the most recent source-mutation candidate from disk."""
        paths = sorted(self.workspace.mutations_dir.glob("source-mutation-*/candidate.json"))
        if not paths:
            raise RuntimeError("No source mutation candidates found.")
        return SourceMutationCandidate.model_validate(json.loads(paths[-1].read_text(encoding="utf-8")))

    def revert_candidate(self, candidate_id: str | None = None) -> SourceMutationCandidate:
        """Revert the latest or named candidate using its stored reverse patch artifact."""
        candidate = self._load_candidate(candidate_id)
        reverse_payload = self._load_patch(candidate.reverse_patch_path)
        if self._matches_payload(reverse_payload):
            candidate.apply_status = "reverted"
            self._write_candidate(candidate)
            return candidate
        manifest = load_manifest(candidate.patch_manifest_path)
        if not matches_fingerprints(self.root, manifest.after_fingerprints, self._sha256):
            raise RuntimeError(
                "Cannot revert source mutation candidate because the workspace no longer matches "
                "the applied candidate state."
            )
        self._apply_patch_payload(reverse_payload)
        candidate.apply_status = "reverted"
        self._write_candidate(candidate)
        return candidate

    def _build_candidate(
        self,
        ranked_slugs: list[str],
    ) -> tuple[SourceMutationCandidate, SourceMutationManifest, list[PatchFileArtifact]]:
        template = self._select_template(ranked_slugs)
        target_path = self.root / template.target_file
        before_content = target_path.read_text(encoding="utf-8")
        after_content = before_content.replace(template.old, template.new, 1)
        if before_content == after_content:
            raise ValueError("Malformed or empty patch candidate.")

        candidate = self._candidate_for(template)
        forward_payload = [self._patch_file(target_path, after_content)]
        reverse_payload = [self._patch_file(target_path, before_content)]
        self._write_patch(candidate.forward_patch_path, forward_payload)
        self._write_patch(candidate.reverse_patch_path, reverse_payload)
        self._write_reasoning(candidate.reasoning_path, template)

        validation = PatchValidationResult(
            touched_files_allowed=validate_touched_files([target_path], self.root),
            reverse_patch_available=bool(reverse_payload),
            non_empty_patch=before_content != after_content,
            single_surface_patch=True,
            has_rationale=bool(template.rationale.strip()),
            has_metric_goal=bool(template.metric_goal.strip()),
        )
        if not all(validation.model_dump().values()):
            candidate.apply_status = "rejected"
            self._write_candidate(candidate)
            raise ValueError("Source mutation candidate failed validation.")

        manifest = SourceMutationManifest(
            candidate_id=candidate.candidate_id,
            mutation_family=template.mutation_family,
            target_files=[template.target_file],
            touched_files=[template.target_file],
            artifact_paths={
                "candidate": candidate.forward_patch_path.replace("forward_patch.json", "candidate.json"),
                "forward_patch": candidate.forward_patch_path,
                "reverse_patch": candidate.reverse_patch_path,
                "manifest": candidate.patch_manifest_path,
                "reasoning": candidate.reasoning_path,
            },
            selected_tests=list(template.selected_tests),
            pre_apply_validation=validation,
            before_fingerprints={template.target_file: self._sha256(before_content)},
            after_fingerprints={template.target_file: self._sha256(after_content)},
        )
        return candidate, manifest, forward_payload

    def _candidate_for(self, template: SourceMutationTemplate) -> SourceMutationCandidate:
        candidate = SourceMutationCandidate(
            mutation_family=template.mutation_family,
            rationale=template.rationale,
            metric_goal=template.metric_goal,
            target_files=[template.target_file],
            touched_files=[template.target_file],
            forward_patch_path=str(self.workspace.mutation_forward_patch_path("pending")),
            reverse_patch_path=str(self.workspace.mutation_reverse_patch_path("pending")),
            patch_manifest_path=str(self.workspace.mutation_manifest_path("pending")),
            reasoning_path=str(self.workspace.mutation_reasoning_path("pending")),
            selected_tests=list(template.selected_tests),
        )
        candidate.forward_patch_path = str(self.workspace.mutation_forward_patch_path(candidate.candidate_id))
        candidate.reverse_patch_path = str(self.workspace.mutation_reverse_patch_path(candidate.candidate_id))
        candidate.patch_manifest_path = str(self.workspace.mutation_manifest_path(candidate.candidate_id))
        candidate.reasoning_path = str(self.workspace.mutation_reasoning_path(candidate.candidate_id))
        return candidate

    def _select_template(self, ranked_slugs: list[str]) -> SourceMutationTemplate:
        if ranked_slugs and ranked_slugs[0] == "prompt_injection":
            return TEMPLATES[1]
        return TEMPLATES[0]

    def _load_candidate(self, candidate_id: str | None) -> SourceMutationCandidate:
        if candidate_id is None:
            return self.latest_candidate()
        path = self.workspace.mutation_candidate_path(candidate_id)
        if not path.exists():
            raise RuntimeError(f"Mutation candidate not found: {candidate_id}")
        return SourceMutationCandidate.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def _load_patch(self, path_str: str) -> list[PatchFileArtifact]:
        payload = json.loads(Path(path_str).read_text(encoding="utf-8"))
        return [PatchFileArtifact.model_validate(item) for item in payload["files"]]

    def _apply_patch_payload(self, payload: list[PatchFileArtifact]) -> None:
        for item in payload:
            path = self.root / item.path
            path.write_text(item.content, encoding="utf-8")

    def _matches_payload(self, payload: list[PatchFileArtifact]) -> bool:
        for item in payload:
            path = self.root / item.path
            if not path.exists() or path.read_text(encoding="utf-8") != item.content:
                return False
        return True

    def _write_candidate(self, candidate: SourceMutationCandidate) -> None:
        path = self.workspace.mutation_candidate_path(candidate.candidate_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(candidate.model_dump_json(indent=2), encoding="utf-8")

    def _write_manifest(self, manifest: SourceMutationManifest) -> None:
        path = self.workspace.mutation_manifest_path(manifest.candidate_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    def _write_patch(self, path_str: str, payload: list[PatchFileArtifact]) -> None:
        path = Path(path_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"files": [item.model_dump(mode="json") for item in payload]}, indent=2),
            encoding="utf-8",
        )

    def _write_reasoning(self, path_str: str, template: SourceMutationTemplate) -> None:
        path = Path(path_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"# {template.mutation_family}\n\n{template.rationale}\n\nMetric goal: {template.metric_goal}\n",
            encoding="utf-8",
        )

    def _patch_file(self, path: Path, content: str) -> PatchFileArtifact:
        return PatchFileArtifact(
            path=path.relative_to(self.root).as_posix(),
            content=content,
            sha256=self._sha256(content),
        )

    def _sha256(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
