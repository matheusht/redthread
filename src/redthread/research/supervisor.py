"""Phase 2 supervisor over offense, regression, and control lanes."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from redthread.config.settings import AlgorithmType, RedThreadSettings
from redthread.research.baseline import run_batch
from redthread.research.calibration import load_calibration
from redthread.research.checkpoints import CheckpointStore
from redthread.research.ledger import ResearchLedger
from redthread.research.models import ResearchBatchSummary, SupervisorCycleSummary
from redthread.research.objectives import ensure_config
from redthread.research.runtime import apply_runtime_overrides
from redthread.research.scheduler import PhaseTwoScheduler
from redthread.research.workspace import ResearchWorkspace


class PhaseTwoResearchHarness:
    """Run supervisor-controlled multi-lane research cycles."""

    def __init__(self, settings: RedThreadSettings, root: Path) -> None:
        self.root = root
        self.workspace = ResearchWorkspace(root)
        self.workspace.ensure_layout()
        self.settings = apply_runtime_overrides(self.workspace.research_settings(settings), root)
        self.config_path = self.workspace.runtime_config_path
        self.results_path = self.workspace.results_path
        self.config = ensure_config(self.config_path, self.workspace.template_config_path)
        self.ledger = ResearchLedger(self.results_path)
        self.checkpoints = CheckpointStore(self.workspace.checkpoints_dir)
        self.scheduler = PhaseTwoScheduler(self.config)
        self.calibration = load_calibration(
            self.results_path,
            self.workspace.baseline_registry_path,
            self.config,
        )

    async def run_cycle(
        self,
        baseline_first: bool,
        algorithm_override: AlgorithmType | None = None,
    ) -> SupervisorCycleSummary:
        """Run one supervised cycle across all configured lanes."""
        started_at = datetime.now(timezone.utc)
        lane_summaries: list[ResearchBatchSummary] = []

        if baseline_first:
            baseline = await run_batch(
                self.settings,
                self.config.benchmark_objectives,
                mode="baseline",
                checkpoint_store=self.checkpoints,
                checkpoint_id="phase2-baseline",
                algorithm_override=algorithm_override,
            )
            self.ledger.append(baseline, status="keep", description="phase2 baseline before supervised cycle")
            self.calibration = load_calibration(
                self.results_path,
                self.workspace.baseline_registry_path,
                self.config,
            )

        for lane in self.scheduler.lanes():
            objectives = self.scheduler.objectives_for_lane(lane)
            summary = await run_batch(
                self.settings,
                objectives,
                mode="supervised_lane",
                lane=lane.lane,
                checkpoint_store=self.checkpoints,
                checkpoint_id=f"phase2-{lane.lane}",
                algorithm_override=algorithm_override,
            )
            self.ledger.append(summary, status="keep", description=f"phase2 {lane.lane} lane")
            lane_summaries.append(summary)

        cycle = self._decide(lane_summaries, started_at)
        self.ledger.append_decision(cycle)
        return cycle

    def _decide(
        self,
        lane_summaries: list[ResearchBatchSummary],
        started_at: datetime,
    ) -> SupervisorCycleSummary:
        """Apply the Phase 2 control gate and pick the winning lane."""
        by_lane = {summary.lane or "unknown": summary for summary in lane_summaries}
        control = by_lane.get("control")
        offense = by_lane.get("offense")
        regression = by_lane.get("regression")

        control_limit_asr = (
            self.calibration.control_max_average_asr
            if self.calibration is not None
            else self.config.control_max_average_asr
        )
        control_limit_score = (
            self.calibration.control_max_average_score
            if self.calibration is not None
            else self.config.control_max_average_score
        )
        control_ok = bool(
            control
            and control.average_asr <= control_limit_asr
            and control.average_score <= control_limit_score
        )

        candidates = [summary for summary in lane_summaries if summary.lane != "control"]
        winner = max(candidates, key=lambda summary: summary.composite_score) if candidates else None

        accepted = bool(winner and control_ok)
        rationale = "rejected cycle; control lane exceeded thresholds or no candidate lane produced output"
        if accepted and winner:
            rationale = f"accepted {winner.lane} lane; control within thresholds"

        if accepted and winner and offense and regression and control:
            rationale = (
                f"accepted {winner.lane} lane; offense={offense.composite_score:.2f}, "
                f"regression={regression.composite_score:.2f}, "
                f"control_asr={control.average_asr:.2%}/{control_limit_asr:.2%}, "
                f"control_score={control.average_score:.2f}/{control_limit_score:.2f}"
            )
        elif control:
            rationale = (
                f"rejected cycle; control_asr={control.average_asr:.2%}/{control_limit_asr:.2%}, "
                f"control_score={control.average_score:.2f}/{control_limit_score:.2f}"
            )

        return SupervisorCycleSummary(
            run_id=f"supervisor-{uuid4().hex[:8]}",
            accepted=accepted,
            winning_lane=winner.lane if winner and winner.lane else "none",
            rationale=rationale,
            lane_summaries=lane_summaries,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )
