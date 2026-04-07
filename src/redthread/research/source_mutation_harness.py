"""Research harness for bounded source mutation cycles."""

from __future__ import annotations

import json
from pathlib import Path

from redthread.config.settings import AlgorithmType, RedThreadSettings
from redthread.research.history import ObjectiveHistoryAnalyzer
from redthread.research.models import PhaseThreeProposal
from redthread.research.phase3 import PhaseThreeHarness
from redthread.research.source_mutation_models import SourceMutationCandidate
from redthread.research.source_mutation_worker import SourceMutationWorker
from redthread.research.workspace import ResearchWorkspace


class SourceMutationHarness:
    """Generate one source mutation, then evaluate it through Phase 3."""

    def __init__(self, settings: RedThreadSettings, root: Path) -> None:
        self.settings = settings
        self.root = root
        self.workspace = ResearchWorkspace(root)
        self.workspace.ensure_layout()
        self.worker = SourceMutationWorker(root)
        self.phase3 = PhaseThreeHarness(settings, root)

    async def run_cycle(
        self,
        baseline_first: bool,
        algorithm_override: AlgorithmType | None = None,
    ) -> tuple[SourceMutationCandidate, PhaseThreeProposal]:
        """Apply one bounded source mutation and emit a normal Phase 3 proposal."""
        ranked = ObjectiveHistoryAnalyzer(self.workspace.results_path).rank()
        candidate = self.worker.generate_and_apply([item.slug for item in ranked])
        proposal = await self.phase3.run_cycle(
            baseline_first=baseline_first,
            algorithm_override=algorithm_override,
        )
        proposal.mutation_candidate_id = candidate.candidate_id
        proposal.mutation_family = candidate.mutation_family
        proposal.mutation_touched_files = list(candidate.touched_files)
        proposal.mutation_selected_tests = list(candidate.selected_tests)
        proposal.mutation_forward_patch_ref = candidate.forward_patch_path
        proposal.mutation_reverse_patch_ref = candidate.reverse_patch_path
        proposal.promotion_eligibility_status = (
            "pending_phase3_accept"
            if proposal.recommended_action == "accept"
            else "rejected_by_supervisor"
        )
        self.workspace.proposal_path(proposal.proposal_id).write_text(
            json.dumps(proposal.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )
        return candidate, proposal

    def inspect_latest(self) -> SourceMutationCandidate:
        """Return the latest source mutation candidate."""
        return self.worker.latest_candidate()

    def revert_latest(self) -> SourceMutationCandidate:
        """Revert the latest source mutation using stored reverse artifacts."""
        return self.worker.revert_candidate()
