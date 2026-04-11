"""Sealed replay fixture definitions for defense validation."""

from __future__ import annotations

from dataclasses import dataclass, field

from redthread.core.defense_assets import (
    BENIGN_DEFENSE_PACK,
    BenignDefenseCase,
    build_guardrail_replay_prompt,
)

_DEFAULT_SUITE_ID = "default-defense-replay-v1"


@dataclass(frozen=True)
class ExploitReplayFixture:
    """Exploit case replayed against a patched target."""

    case_id: str
    attack_payload: str
    rubric_name: str = "authorization_bypass"


@dataclass(frozen=True)
class DefenseReplaySuite:
    """One named replay suite containing exploit + benign cases."""

    suite_id: str
    exploit: ExploitReplayFixture
    benign_cases: tuple[BenignDefenseCase, ...] = field(default_factory=tuple)


def build_default_replay_suite(attack_payload: str) -> DefenseReplaySuite:
    """Return the default sealed replay suite for one isolated exploit."""
    return DefenseReplaySuite(
        suite_id=_DEFAULT_SUITE_ID,
        exploit=ExploitReplayFixture(case_id="exploit_replay", attack_payload=attack_payload),
        benign_cases=tuple(BENIGN_DEFENSE_PACK),
    )


def render_replay_prompt(guardrail_clause: str, user_prompt: str, base_system_prompt: str = "") -> str:
    """Render a replay prompt using the shared runtime guardrail formatting path."""
    return build_guardrail_replay_prompt(guardrail_clause, user_prompt, base_system_prompt)


__all__ = [
    "DefenseReplaySuite",
    "ExploitReplayFixture",
    "build_default_replay_suite",
    "render_replay_prompt",
]
