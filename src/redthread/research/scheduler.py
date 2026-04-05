"""Phase 2 lane scheduler."""

from __future__ import annotations

from redthread.research.models import ResearchConfig, ResearchLaneConfig, ResearchObjective


class PhaseTwoScheduler:
    """Resolve objectives for supervisor lanes from config."""

    def __init__(self, config: ResearchConfig) -> None:
        self.config = config

    def lanes(self) -> list[ResearchLaneConfig]:
        """Return lane configs, creating defaults if missing."""
        if self.config.lane_configs:
            return self.config.lane_configs
        return [
            ResearchLaneConfig(
                lane="offense",
                source="experiment",
                objective_slugs=["authorization_bypass", "system_prompt_exfiltration"],
            ),
            ResearchLaneConfig(
                lane="regression",
                source="experiment",
                objective_slugs=["sensitive_info_exfiltration", "prompt_injection"],
            ),
            ResearchLaneConfig(
                lane="control",
                source="benchmark",
                objective_slugs=[
                    "prompt_injection",
                    "authorization_bypass",
                    "sensitive_info_exfiltration",
                    "system_prompt_exfiltration",
                ],
            ),
        ]

    def objectives_for_lane(self, lane: ResearchLaneConfig) -> list[ResearchObjective]:
        """Resolve configured slugs to concrete objectives."""
        pool = (
            self.config.benchmark_objectives
            if lane.source == "benchmark"
            else self.config.experiment_objectives
        )
        index = {objective.slug: objective for objective in pool}
        return [
            index[slug]
            for slug in lane.objective_slugs
            if slug in index
        ]
