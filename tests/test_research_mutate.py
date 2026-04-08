from __future__ import annotations

import json
from pathlib import Path

from pytest import MonkeyPatch

from redthread.config.settings import RedThreadSettings
from redthread.research.models import PhaseThreeProposal, SupervisorCycleSummary
from redthread.research.phase3 import PhaseThreeHarness
from redthread.research.source_mutation_harness import SourceMutationHarness
from redthread.research.source_mutation_registry import SourceMutationTemplate
from redthread.research.source_mutation_worker import SourceMutationWorker
from tests.research_mutation_helpers import (
    scaffold_blocked_target,
    scaffold_prompt_profiles_target,
    scaffold_source_mutation_targets,
)


def test_patch_touching_blocked_file_is_rejected(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    scaffold_blocked_target(tmp_path)
    monkeypatch.setattr(
        "redthread.research.source_mutation_worker.TEMPLATES",
        (
            SourceMutationTemplate(
                mutation_family="blocked",
                rationale="test",
                metric_goal="test",
                target_file="src/redthread/memory/index.py",
                old="blocked",
                new="mutated",
                selected_tests=("tests/test_research_mutate.py",),
            ),
        ),
    )

    try:
        SourceMutationWorker(tmp_path).generate_and_apply(["authorization_bypass"])
    except ValueError as exc:
        assert "failed validation" in str(exc)
    else:
        raise AssertionError("expected blocked target rejection")


def test_mutation_worker_only_selects_approved_files(tmp_path: Path) -> None:
    scaffold_source_mutation_targets(tmp_path)

    candidate = SourceMutationWorker(tmp_path).generate_and_apply(["authorization_bypass"])

    assert candidate.target_files == ["src/redthread/core/pair.py"]


def test_forward_and_reverse_patch_artifacts_are_written_before_apply(tmp_path: Path) -> None:
    scaffold_source_mutation_targets(tmp_path)
    path = tmp_path / "src" / "redthread" / "core" / "pair.py"
    worker = SourceMutationWorker(tmp_path)

    candidate = worker.generate_and_apply(["authorization_bypass"])

    assert Path(candidate.forward_patch_path).exists()
    assert Path(candidate.reverse_patch_path).exists()
    assert path.read_text(encoding="utf-8") != 'PAIR = "5. Escalate gradually. Establish rapport before making the core malicious request."\nTAP = "build rapport and appeal to shared values",\n'


def test_reverse_patch_restores_prior_file_state_exactly(tmp_path: Path) -> None:
    scaffold_source_mutation_targets(tmp_path)
    path = tmp_path / "src" / "redthread" / "core" / "tap.py"
    original = path.read_text(encoding="utf-8")
    worker = SourceMutationWorker(tmp_path)
    candidate = worker.generate_and_apply(["prompt_injection"])

    worker.revert_candidate(candidate.candidate_id)

    assert path.read_text(encoding="utf-8") == original


def test_malformed_or_empty_patch_candidates_are_rejected(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    scaffold_prompt_profiles_target(tmp_path)
    monkeypatch.setattr(
        "redthread.research.source_mutation_worker.TEMPLATES",
        (
            SourceMutationTemplate(
                mutation_family="empty",
                rationale="test",
                metric_goal="test",
                target_file="src/redthread/research/prompt_profiles.py",
                old="does-not-exist",
                new="replacement",
                selected_tests=("tests/test_research_mutate.py",),
            ),
        ),
    )

    try:
        SourceMutationWorker(tmp_path).generate_and_apply(["authorization_bypass"])
    except ValueError as exc:
        assert "Malformed or empty patch candidate" in str(exc)
    else:
        raise AssertionError("expected empty patch rejection")


def test_source_mutation_cycle_emits_phase3_patch_refs(tmp_path: Path) -> None:
    scaffold_source_mutation_targets(tmp_path)
    worker = SourceMutationWorker(tmp_path)
    candidate = worker.generate_and_apply(["authorization_bypass"])
    phase3 = PhaseThreeHarness.__new__(PhaseThreeHarness)
    phase3.workspace = worker.workspace

    refs = phase3._mutation_refs()

    assert candidate.forward_patch_path in refs
    assert candidate.reverse_patch_path in refs
    assert candidate.patch_manifest_path in refs


def test_accepted_source_mutation_still_does_not_affect_production_before_promote(tmp_path: Path) -> None:
    scaffold_source_mutation_targets(tmp_path)

    SourceMutationWorker(tmp_path).generate_and_apply(["authorization_bypass"])

    assert not (tmp_path / "memory" / "MEMORY.md").exists()


def test_rejected_mutation_can_be_reverted_cleanly_from_stored_artifacts(tmp_path: Path) -> None:
    scaffold_source_mutation_targets(tmp_path)
    path = tmp_path / "src" / "redthread" / "core" / "pair.py"
    worker = SourceMutationWorker(tmp_path)
    candidate = worker.generate_and_apply(["authorization_bypass"])

    reverted = worker.revert_candidate(candidate.candidate_id)

    assert reverted.apply_status == "reverted"
    assert "internal verification" not in path.read_text(encoding="utf-8")


def test_revert_fails_without_overwriting_later_edits(tmp_path: Path) -> None:
    scaffold_source_mutation_targets(tmp_path)
    path = tmp_path / "src" / "redthread" / "core" / "pair.py"
    worker = SourceMutationWorker(tmp_path)
    candidate = worker.generate_and_apply(["authorization_bypass"])
    diverged = 'PROMPT = "manual change after apply"\n'
    path.write_text(diverged, encoding="utf-8")

    try:
        worker.revert_candidate(candidate.candidate_id)
    except RuntimeError as exc:
        assert "no longer matches the applied candidate state" in str(exc)
    else:
        raise AssertionError("expected divergence to block revert")

    assert path.read_text(encoding="utf-8") == diverged


def test_idempotent_inspect_and_revert_behavior(tmp_path: Path) -> None:
    scaffold_source_mutation_targets(tmp_path)
    worker = SourceMutationWorker(tmp_path)
    candidate = worker.generate_and_apply(["authorization_bypass"])

    inspected = worker.latest_candidate()
    reverted_once = worker.revert_candidate(candidate.candidate_id)
    reverted_twice = worker.revert_candidate(candidate.candidate_id)

    assert inspected.candidate_id == candidate.candidate_id
    assert reverted_once.apply_status == "reverted"
    assert reverted_twice.apply_status == "reverted"
    assert json.loads(Path(candidate.reverse_patch_path).read_text(encoding="utf-8"))["files"]


async def test_source_mutation_harness_enriches_proposal_artifact(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    scaffold_source_mutation_targets(tmp_path)

    async def stub_phase3_run_cycle(
        self: object,
        baseline_first: bool,
        algorithm_override: object | None = None,
    ) -> PhaseThreeProposal:
        harness = self
        proposal = PhaseThreeProposal(
            proposal_id="proposal-123",
            session_tag="tag",
            session_branch="autoresearch/tag",
            session_base_commit="abc1234",
            accepted=True,
            recommended_action="accept",
            rationale="ok",
            cycle=SupervisorCycleSummary(run_id="supervisor-1", accepted=True, winning_lane="offense", rationale="ok"),
            runtime_config_path=str(harness.config_path),
            checkpoint_refs=[],
            mutation_refs=[],
            research_memory_dir=str(harness.workspace.research_memory_dir),
            eligible_trace_ids=[],
        )
        harness.workspace.proposal_path(proposal.proposal_id).write_text(
            proposal.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return proposal

    monkeypatch.setattr("redthread.research.phase3.PhaseThreeHarness.run_cycle", stub_phase3_run_cycle)

    harness = SourceMutationHarness(RedThreadSettings(), tmp_path)

    candidate, proposal = await harness.run_cycle(baseline_first=False)

    saved = json.loads(harness.workspace.proposal_path(proposal.proposal_id).read_text(encoding="utf-8"))
    assert saved["mutation_candidate_id"] == candidate.candidate_id
    assert saved["mutation_phase"] == "phase5"
    assert saved["mutation_family"] == candidate.mutation_family
    assert saved["mutation_forward_patch_ref"] == candidate.forward_patch_path
    assert saved["promotion_eligibility_status"] == "pending_phase3_accept"
