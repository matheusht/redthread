"""Campaign planning models for risk and strategy resolution."""

from __future__ import annotations

from pydantic import BaseModel, Field

from redthread.orchestration.models.attack_strategy import AttackStrategySpec
from redthread.orchestration.models.authorized_scope import AuthorizedScope
from redthread.orchestration.models.risk_plugin import RiskPlugin


class PlannedRisk(BaseModel):
    """A resolved risk plugin with compatible selected strategies."""

    plugin: RiskPlugin
    strategy_ids: list[str] = Field(default_factory=list)


class CampaignPlan(BaseModel):
    """Deterministic plan produced before campaign execution."""

    objective: str
    target_system_prompt: str
    rubric_name: str = "authorization_bypass"
    num_personas: int = 3
    risks: list[PlannedRisk] = Field(default_factory=list)
    strategies: list[AttackStrategySpec] = Field(default_factory=list)
    scope: AuthorizedScope = Field(default_factory=AuthorizedScope)

    @property
    def risk_ids(self) -> list[str]:
        """Return risk ids in plan order."""
        return [risk.plugin.id for risk in self.risks]

    @property
    def strategy_ids(self) -> list[str]:
        """Return selected strategy ids in stable order."""
        return [strategy.id for strategy in self.strategies]

    def summary_lines(self) -> list[str]:
        """Return deterministic operator-readable summary lines."""
        lines = [
            f"Objective: {self.objective}",
            f"Rubric: {self.rubric_name}",
            f"Personas: {self.num_personas}",
            f"Risks: {', '.join(self.risk_ids) if self.risks else '(none)'}",
            f"Strategies: {', '.join(self.strategy_ids) if self.strategies else '(none)'}",
            f"Scope targets: {', '.join(self.scope.target_ids) if self.scope.target_ids else '(none)' }",
        ]
        for risk in self.risks:
            strategy_ids = ", ".join(risk.strategy_ids) if risk.strategy_ids else "(none)"
            lines.append(f"- {risk.plugin.id}: {strategy_ids}")
        return lines
