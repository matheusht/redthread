"""Attack strategy contracts for campaign planning."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class StrategyFamily(str, Enum):
    """Execution family for an attack strategy."""

    STATIC_REPLAY = "static_replay"
    SINGLE_TURN = "single_turn"
    MULTI_TURN = "multi_turn"
    TREE_SEARCH = "tree_search"
    LAYERED = "layered"


class CostLevel(str, Enum):
    """Rough runtime and token cost for planning."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AttackStrategySpec(BaseModel):
    """RedThread-native description of how to attack a risk plugin."""

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$", min_length=1)
    name: str = Field(min_length=1)
    family: StrategyFamily
    description: str = ""
    compatible_plugin_ids: list[str] = Field(default_factory=list)
    cost_level: CostLevel = CostLevel.MEDIUM
    max_turns: int | None = Field(default=None, ge=1)
    uses_llm_attacker: bool = True
    supports_layering: bool = False
    requires_multi_turn_target: bool = False
    requires_authorized_scope: bool = True
    safety_requirements: list[str] = Field(default_factory=list)

    def is_compatible_with(self, plugin_id: str) -> bool:
        """Return whether this strategy can run against the plugin id."""
        return not self.compatible_plugin_ids or plugin_id in self.compatible_plugin_ids
