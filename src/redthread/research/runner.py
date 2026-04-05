"""High-level Phase 1 research harness orchestration."""

from __future__ import annotations

from pathlib import Path

from redthread.config.settings import RedThreadSettings
from redthread.research.baseline import run_batch
from redthread.research.ledger import ResearchLedger
from redthread.research.models import ResearchBatchSummary
from redthread.research.objectives import ensure_config
from redthread.research.runtime import apply_runtime_overrides


class PhaseOneResearchHarness:
    """Creates config/ledger files and runs baseline or bounded experiment batches."""

    def __init__(
        self,
        settings: RedThreadSettings,
        root: Path,
    ) -> None:
        self.settings = apply_runtime_overrides(settings, root)
        self.root = root
        self.config_path = root / "autoresearch" / "config.json"
        self.results_path = root / "autoresearch" / "results.tsv"
        self.config = ensure_config(self.config_path)
        self.ledger = ResearchLedger(self.results_path)

    async def run_baseline(self) -> ResearchBatchSummary:
        """Run the frozen benchmark pack and append it to the ledger."""
        summary = await run_batch(
            self.settings,
            self.config.benchmark_objectives,
            mode="baseline",
        )
        self.ledger.append(summary, status="keep", description="phase1 frozen benchmark pack")
        return summary

    async def run_experiments(
        self,
        cycles: int,
        baseline_first: bool,
    ) -> list[ResearchBatchSummary]:
        """Run a bounded number of experiment cycles and append them to the ledger."""
        summaries: list[ResearchBatchSummary] = []
        if baseline_first:
            summaries.append(await self.run_baseline())

        total_cycles = cycles if cycles > 0 else 1
        for cycle in range(1, total_cycles + 1):
            summary = await run_batch(
                self.settings,
                self.config.experiment_objectives,
                mode="experiment",
            )
            self.ledger.append(
                summary,
                status="keep",
                description=f"phase1 bounded experiment cycle {cycle}",
            )
            summaries.append(summary)
        return summaries
