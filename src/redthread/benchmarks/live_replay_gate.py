"""Deferred live benchmark replay gate design."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

LIVE_REPLAY_ACKNOWLEDGEMENT = "I understand this benchmark replay may contact an approved live target"
LIVE_REPLAY_DEFERRED_MESSAGE = (
    "live benchmark replay is deferred; use local-dev sealed harness. "
    "Future live replay requires manifest allowlist and typed acknowledgement."
)


class BenchmarkLiveReplayGatePlan(BaseModel):
    """Prompt-safe contract for future live benchmark replay eligibility."""

    status: Literal["deferred"] = "deferred"
    target_id: str = Field(min_length=1)
    required_manifest_allowlist: list[str] = Field(default_factory=list)
    required_acknowledgement: str = LIVE_REPLAY_ACKNOWLEDGEMENT
    legacy_flag_sufficient: bool = False
    raw_prompt_policy: str = "raw prompt bodies stay in the private benchmark vault"
    execution_policy: str = "no live provider calls until a future implementation consumes this gate"

    @property
    def is_acknowledged(self) -> bool:
        """Return whether a future request has all acknowledgement inputs modeled."""
        return False


def build_live_replay_gate_plan(
    *,
    target_id: str,
    allowed_target_ids: list[str] | None = None,
) -> BenchmarkLiveReplayGatePlan:
    """Build the non-executing gate plan for future live replay work."""
    return BenchmarkLiveReplayGatePlan(
        target_id=target_id,
        required_manifest_allowlist=list(allowed_target_ids or []),
    )
