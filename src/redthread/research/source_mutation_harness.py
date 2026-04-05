"""Research harness for bounded source mutation cycles."""

from __future__ import annotations

from pathlib import Path

from redthread.config.settings import RedThreadSettings
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

    async def run_cycle(self, baseline_first: bool) -> tuple[SourceMutationCandidate, PhaseThreeProposal]:
        """Apply one bounded source mutation and emit a normal Phase 3 proposal."""
        ranked = ObjectiveHistoryAnalyzer(self.workspace.results_path).rank()
        candidate = self.worker.generate_and_apply([item.slug for item in ranked])
        proposal = await self.phase3.run_cycle(baseline_first=baseline_first)
        return candidate, proposal

    def inspect_latest(self) -> SourceMutationCandidate:
        """Return the latest source mutation candidate."""
        return self.worker.latest_candidate()

    def revert_latest(self) -> SourceMutationCandidate:
        """Revert the latest source mutation using stored reverse artifacts."""
        return self.worker.revert_candidate()
