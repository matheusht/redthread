"""Campaign planning bridge for reviewed benchmark fixtures."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, Field

from redthread.benchmarks.jailbreak_fixtures import JailbreakBenchmarkFixture
from redthread.orchestration.campaign_planning import CampaignPlanningError, build_campaign_plan
from redthread.orchestration.models import CampaignPlan


class BenchmarkCampaignDraft(BaseModel):
    """Dry campaign plan plus benchmark fixture lineage."""

    plan: CampaignPlan
    fixtures: list[JailbreakBenchmarkFixture] = Field(default_factory=list)
    benchmark_metadata: list[dict[str, str]] = Field(default_factory=list)
    blocked_fixture_ids: list[str] = Field(default_factory=list)

    def summary_lines(self) -> list[str]:
        """Return operator-readable dry-run summary lines."""
        lines = [
            "Benchmark: jailbreak fixture pack",
            f"Executable fixtures: {len(self.fixtures)}",
            f"Blocked fixtures: {len(self.blocked_fixture_ids)}",
            *self.plan.summary_lines(),
        ]
        for fixture in self.fixtures:
            lines.append(
                f"- fixture {fixture.id}: {fixture.family} -> "
                f"{fixture.risk_plugin_id}/{fixture.strategy_id}"
            )
        return lines


def build_benchmark_campaign_draft(
    fixtures: Sequence[JailbreakBenchmarkFixture],
    *,
    objective: str,
    target_id: str,
    target_system_prompt: str = "",
    allow_live_target: bool = False,
) -> BenchmarkCampaignDraft:
    """Convert approved benchmark fixtures into a deterministic campaign plan."""
    if not target_id:
        msg = "benchmark campaign target_id is required"
        raise CampaignPlanningError(msg)
    if not allow_live_target and target_id != "local-dev":
        msg = "benchmark campaigns require local-dev target unless live target is authorized"
        raise CampaignPlanningError(msg)
    selected = _approved_fixtures(fixtures)
    risks = _unique([fixture.risk_plugin_id for fixture in selected])
    strategies = _unique([fixture.strategy_id for fixture in selected])
    plan = build_campaign_plan(
        {
            "objective": objective,
            "target_system_prompt": target_system_prompt,
            "rubric_name": selected[0].rubric_id,
            "risks": risks,
            "strategies": {"include": strategies},
            "scope": {"target_ids": [target_id]},
        }
    )
    return BenchmarkCampaignDraft(
        plan=plan,
        fixtures=selected,
        benchmark_metadata=[fixture.lineage_metadata() for fixture in selected],
        blocked_fixture_ids=[fixture.id for fixture in fixtures if not fixture.is_executable],
    )


def _approved_fixtures(
    fixtures: Sequence[JailbreakBenchmarkFixture],
) -> list[JailbreakBenchmarkFixture]:
    selected = [fixture for fixture in fixtures if fixture.is_executable]
    if not selected:
        msg = "no approved benchmark fixtures selected for execution"
        raise CampaignPlanningError(msg)
    return selected


def _unique(values: Sequence[str]) -> list[str]:
    return sorted(set(values))
