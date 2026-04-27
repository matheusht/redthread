"""Shared strategy runner contracts."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from redthread.models import AttackTrace
from redthread.orchestration.models import CampaignPlan


class StrategyExecutionError(ValueError):
    """Raised when a strategy adapter cannot execute a planned slice."""


class StrategyRunBudget(BaseModel):
    """Small execution budget passed into a strategy adapter."""

    max_prompts: int = Field(default=1, ge=1)
    max_turns: int | None = Field(default=None, ge=1)


class StrategyTarget(Protocol):
    """Minimal target boundary used by strategy adapters."""

    async def send(self, prompt: str, conversation_id: str = "") -> str: ...


class AttackStrategyRunner(Protocol):
    """Narrow wrapper around one RedThread attack strategy."""

    strategy_id: str

    async def run(
        self,
        plan: CampaignPlan,
        *,
        target: StrategyTarget,
        risk_plugin_id: str | None = None,
        budget: StrategyRunBudget | None = None,
        target_id: str | None = None,
    ) -> AttackTrace: ...
