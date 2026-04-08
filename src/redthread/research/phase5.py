"""Phase 5 bounded source mutation automation over offense modules."""

from __future__ import annotations

from pathlib import Path

from redthread.config.settings import AlgorithmType, RedThreadSettings
from redthread.research.models import PhaseThreeProposal
from redthread.research.source_mutation_harness import SourceMutationHarness
from redthread.research.source_mutation_models import SourceMutationCandidate


class PhaseFiveHarness:
    """Formal Phase 5 wrapper around the bounded source mutation harness."""

    def __init__(self, settings: RedThreadSettings, root: Path) -> None:
        self._harness = SourceMutationHarness(settings, root, mutation_phase="phase5")
        self.workspace = self._harness.workspace

    async def run_cycle(
        self,
        baseline_first: bool,
        algorithm_override: AlgorithmType | None = None,
    ) -> tuple[SourceMutationCandidate, PhaseThreeProposal]:
        """Apply one bounded source mutation and evaluate it through Phase 3."""
        return await self._harness.run_cycle(
            baseline_first=baseline_first,
            algorithm_override=algorithm_override,
        )

    def inspect_latest(self) -> SourceMutationCandidate:
        """Return the latest source mutation candidate."""
        return self._harness.inspect_latest()

    def revert_latest(self) -> SourceMutationCandidate:
        """Revert the latest source mutation using stored reverse artifacts."""
        return self._harness.revert_latest()
