"""Template-driven bounded source mutation worker."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

from redthread.research.source_mutation_artifacts import (
    apply_patch_payload,
    load_patch,
    matches_payload,
    patch_file,
    sha256,
    write_candidate,
    write_manifest,
    write_patch,
    write_reasoning,
)
from redthread.research.source_mutation_models import (
    CandidateValidationOutcome,
    PatchFileArtifact,
    PatchValidationResult,
    SourceMutationCandidate,
    SourceMutationManifest,
)
from redthread.research.source_mutation_policy import validate_touched_files
from redthread.research.source_mutation_registry import TEMPLATES, SourceMutationTemplate
from redthread.research.source_mutation_revert import load_manifest, matches_fingerprints
from redthread.research.source_mutation_selection import select_phase5_template
from redthread.research.workspace import ResearchWorkspace

PreApplyValidator = Callable[[Path, str, str, Path], CandidateValidationOutcome]
TemplateSelector = Callable[[list[str], Sequence[SourceMutationTemplate]], SourceMutationTemplate]


class SourceMutationWorker:
    """Generate, validate, apply, inspect, and revert bounded source mutations."""

    def __init__(
        self,
        root: Path,
        *,
        templates: Sequence[SourceMutationTemplate] | None = None,
        touched_files_validator: Callable[[list[Path], Path], bool] | None = None,
        pre_apply_validator: PreApplyValidator | None = None,
        template_selector: TemplateSelector | None = None,
        mutation_phase: str = "phase5",
    ) -> None:
        self.root = root
        self.workspace = ResearchWorkspace(root)
        self.workspace.ensure_layout()
        self.templates = tuple(templates) if templates is not None else tuple(TEMPLATES)
        self.touched_files_validator = touched_files_validator or validate_touched_files
        self.pre_apply_validator = pre_apply_validator
        self.template_selector = template_selector or select_phase5_template
        self.mutation_phase = mutation_phase

    def generate_and_apply(self, ranked_slugs: list[str]) -> SourceMutationCandidate:
        """Create one candidate, persist all artifacts, then apply it."""
        candidate, manifest, forward_payload = self._build_candidate(ranked_slugs)
        write_candidate(self.workspace.mutation_candidate_path(candidate.candidate_id), candidate)
        write_manifest(self.workspace.mutation_manifest_path(manifest.candidate_id), manifest)
        if candidate.apply_status == "rejected":
            raise ValueError("Source mutation candidate failed validation.")
        self._apply_patch_payload(forward_payload)
        candidate.apply_status = "applied"
        write_candidate(self.workspace.mutation_candidate_path(candidate.candidate_id), candidate)
        return candidate

    def latest_candidate(self) -> SourceMutationCandidate:
        """Load the most recent source-mutation candidate from disk."""
        paths = sorted(self.workspace.mutations_dir.glob("source-mutation-*/candidate.json"))
        if not paths:
            raise RuntimeError("No source mutation candidates found.")
        for path in reversed(paths):
            candidate = SourceMutationCandidate.model_validate_json(path.read_text(encoding="utf-8"))
            if candidate.mutation_phase == self.mutation_phase:
                return candidate
        raise RuntimeError(f"No {self.mutation_phase} source mutation candidates found.")

    def revert_candidate(self, candidate_id: str | None = None) -> SourceMutationCandidate:
        """Revert the latest or named candidate using its stored reverse patch artifact."""
        candidate = self._load_candidate(candidate_id)
        reverse_payload = load_patch(candidate.reverse_patch_path)
        if self._matches_payload(reverse_payload):
            candidate.apply_status = "reverted"
            write_candidate(self.workspace.mutation_candidate_path(candidate.candidate_id), candidate)
            return candidate
        manifest = load_manifest(candidate.patch_manifest_path)
        if not matches_fingerprints(self.root, manifest.after_fingerprints, sha256):
            raise RuntimeError(
                "Cannot revert source mutation candidate because the workspace no longer matches "
                "the applied candidate state."
            )
        self._apply_patch_payload(reverse_payload)
        candidate.apply_status = "reverted"
        write_candidate(self.workspace.mutation_candidate_path(candidate.candidate_id), candidate)
        return candidate

    def _build_candidate(
        self,
        ranked_slugs: list[str],
    ) -> tuple[SourceMutationCandidate, SourceMutationManifest, list[PatchFileArtifact]]:
        template = self.template_selector(ranked_slugs, self.templates)
        target_path = self.root / template.target_file
        before_content = target_path.read_text(encoding="utf-8")
        after_content = before_content.replace(template.old, template.new, 1)
        if before_content == after_content:
            raise ValueError("Malformed or empty patch candidate.")

        candidate = self._candidate_for(template)
        forward_payload = [patch_file(self.root, target_path, after_content)]
        reverse_payload = [patch_file(self.root, target_path, before_content)]
        write_patch(Path(candidate.forward_patch_path), forward_payload)
        write_patch(Path(candidate.reverse_patch_path), reverse_payload)
        write_reasoning(Path(candidate.reasoning_path), template.mutation_family, template.rationale, template.metric_goal)
        extra_validation = self._run_pre_apply_validator(target_path, before_content, after_content)

        validation = PatchValidationResult(
            touched_files_allowed=self.touched_files_validator([target_path], self.root),
            reverse_patch_available=bool(reverse_payload),
            non_empty_patch=before_content != after_content,
            single_surface_patch=True,
            has_rationale=bool(template.rationale.strip()),
            has_metric_goal=bool(template.metric_goal.strip()),
            validator_passed=extra_validation.passed,
            validator_checks=extra_validation.checks,
        )
        candidate.apply_status = "generated" if validation.all_passed() else "rejected"

        manifest = SourceMutationManifest(
            candidate_id=candidate.candidate_id,
            mutation_phase=self.mutation_phase,
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
            before_fingerprints={template.target_file: sha256(before_content)},
            after_fingerprints={template.target_file: sha256(after_content)},
        )
        return candidate, manifest, forward_payload

    def _candidate_for(self, template: SourceMutationTemplate) -> SourceMutationCandidate:
        candidate = SourceMutationCandidate(
            mutation_phase=self.mutation_phase,
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

    def _load_candidate(self, candidate_id: str | None) -> SourceMutationCandidate:
        if candidate_id is None:
            return self.latest_candidate()
        path = self.workspace.mutation_candidate_path(candidate_id)
        if not path.exists():
            raise RuntimeError(f"Mutation candidate not found: {candidate_id}")
        return SourceMutationCandidate.model_validate_json(path.read_text(encoding="utf-8"))

    def _apply_patch_payload(self, payload: list[PatchFileArtifact]) -> None:
        apply_patch_payload(self.root, payload)

    def _matches_payload(self, payload: list[PatchFileArtifact]) -> bool:
        return matches_payload(self.root, payload)

    def _run_pre_apply_validator(
        self,
        target_path: Path,
        before_content: str,
        after_content: str,
    ) -> CandidateValidationOutcome:
        if self.pre_apply_validator is None:
            return CandidateValidationOutcome(passed=True)
        return self.pre_apply_validator(target_path, before_content, after_content, self.root)
