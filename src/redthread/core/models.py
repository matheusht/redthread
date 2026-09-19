"""Search-state models shared by attack strategies."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


class AttackNode(BaseModel):
    """A single node in a TAP attack tree."""

    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    parent_id: str | None = None
    depth: int = 0
    attacker_prompt: str = ""
    target_response: str = ""
    score: float = 0.0
    improvement_rationale: str = ""
    is_pruned: bool = False
    pruned_reason: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MCTSNode(BaseModel):
    """A node in the GS-MCTS search tree."""

    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    parent_id: str | None = None
    depth: int = 0
    strategy: str = ""
    attacker_prompt: str = ""
    target_response: str = ""
    visit_count: int = 0
    total_reward: float = 0.0
    score: float = 0.0
    is_terminal: bool = False
    is_expanded: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CrescendoTurn(BaseModel):
    """A single turn in a Crescendo escalation dialogue."""

    turn_number: int
    escalation_level: int = 0
    attacker_prompt: str
    target_response: str
    score: float = 0.0
    backtracked: bool = False
    backtrack_attempts: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


__all__ = ["AttackNode", "CrescendoTurn", "MCTSNode"]
