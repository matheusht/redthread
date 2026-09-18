"""Run each named launch strategy through the normal campaign runner."""

from collections.abc import Awaitable, Callable, Sequence

from redthread.models import CampaignResult

from .models import StrategyCampaign

CampaignRunner = Callable[[str], Awaitable[CampaignResult]]


async def run_launch_campaigns(
    runner: CampaignRunner,
    *,
    strategies: Sequence[str] = ("pair", "tap", "crescendo"),
) -> dict[str, StrategyCampaign]:
    """Invoke every strategy; capture failure so readiness cannot silently downgrade."""
    outputs: dict[str, StrategyCampaign] = {}
    for strategy_id in strategies:
        try:
            outputs[strategy_id] = StrategyCampaign(
                strategy_id=strategy_id,
                campaign=await runner(strategy_id),
            )
        except Exception as exc:
            outputs[strategy_id] = StrategyCampaign(
                strategy_id=strategy_id,
                error=f"{type(exc).__name__}: {exc}",
            )
    return outputs


__all__ = ["CampaignRunner", "run_launch_campaigns"]
