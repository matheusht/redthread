"""Phase 4 bounded mutation automation over prompt profiles and runtime state."""

from __future__ import annotations

from pathlib import Path

from redthread.config.settings import RedThreadSettings
from redthread.research.history import ObjectiveHistoryAnalyzer
from redthread.research.mutations import MutationCandidate, apply_mutation, next_mutation
from redthread.research.phase3 import PhaseThreeHarness


class PhaseFourHarness:
    """Generate and apply a bounded mutation before running a Phase 3 cycle."""

    def __init__(self, settings: RedThreadSettings, root: Path) -> None:
        self.settings = settings
        self.root = root
        self.autoresearch_dir = root / "autoresearch"
        self.phase3 = PhaseThreeHarness(settings, root)

    async def run_cycle(self, baseline_first: bool) -> tuple[MutationCandidate, object]:
        """Apply the next mutation candidate and evaluate it through Phase 3."""
        ranked = ObjectiveHistoryAnalyzer(self.autoresearch_dir / "results.tsv").rank()
        candidate = next_mutation(self.root, [item.slug for item in ranked])
        apply_mutation(self.root, candidate)
        proposal = await self.phase3.run_cycle(baseline_first=baseline_first)
        return candidate, proposal
