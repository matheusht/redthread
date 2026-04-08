"""Phase 6 bounded defense prompt autoresearch."""

from __future__ import annotations

from pathlib import Path

from redthread.config.settings import AlgorithmType, RedThreadSettings
from redthread.research.defense_source_mutation_policy import validate_defense_touched_files
from redthread.research.defense_source_mutation_registry import (
    DEFENSE_TEMPLATES,
    select_defense_template,
)
from redthread.research.defense_source_mutation_validator import validate_defense_prompt_candidate
from redthread.research.models import PhaseThreeProposal
from redthread.research.source_mutation_harness import SourceMutationHarness
from redthread.research.source_mutation_models import SourceMutationCandidate
from redthread.research.source_mutation_worker import SourceMutationWorker


class PhaseSixHarness:
    """Formal Phase 6 wrapper around bounded defense prompt mutation."""

    def __init__(self, settings: RedThreadSettings, root: Path) -> None:
        worker = SourceMutationWorker(
            root,
            templates=DEFENSE_TEMPLATES,
            touched_files_validator=validate_defense_touched_files,
            pre_apply_validator=validate_defense_prompt_candidate,
            template_selector=select_defense_template,
            mutation_phase="phase6",
        )
        self._harness = SourceMutationHarness(settings, root, worker=worker, mutation_phase="phase6")
        self.workspace = self._harness.workspace

    async def run_cycle(
        self,
        baseline_first: bool,
        algorithm_override: AlgorithmType | None = None,
    ) -> tuple[SourceMutationCandidate, PhaseThreeProposal]:
        """Apply one bounded defense prompt mutation and evaluate it through Phase 3."""
        return await self._harness.run_cycle(
            baseline_first=baseline_first,
            algorithm_override=algorithm_override,
        )

    def inspect_latest(self) -> SourceMutationCandidate:
        """Return the latest phase6 mutation candidate."""
        return self._harness.inspect_latest()

    def revert_latest(self) -> SourceMutationCandidate:
        """Revert the latest phase6 mutation using stored reverse artifacts."""
        return self._harness.revert_latest()
