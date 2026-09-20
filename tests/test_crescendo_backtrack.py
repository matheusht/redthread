"""Tests for Crescendo multi-turn backtracking and refusal exclusion (Issue #130)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from redthread.core.crescendo import CrescendoAttack
from tests.test_crescendo import (
    _make_mocks,
    make_persona,
    make_settings,
    make_verdict,
)


@pytest.mark.asyncio
async def test_crescendo_excludes_refusal_at_backtrack_limit_from_history() -> None:
    """When a turn exhausts all backtrack retries below threshold, it must not poison conversation history."""
    settings = make_settings(
        crescendo_max_turns=2,
        crescendo_backtrack_limit=1,
        crescendo_escalation_threshold=3.0,
    )
    persona = make_persona()

    # Turn 1 succeeds (score 3.5). Turn 2 attempt 1 fails (1.0). Turn 2 attempt 2 (retry) fails (1.0).
    mock_attacker, mock_target, mock_judge = _make_mocks(
        attacker_responses=["opener", "try1", "try2"],
        target_responses=["safe_context", "hard refusal 1", "hard refusal 2"],
        inline_scores=[3.5, 1.0, 1.0],
        final_verdict=make_verdict(score=1.5, is_jailbreak=False),
    )

    with patch("redthread.pyrit_adapters.targets._build_pyrit_target"):
        cres = CrescendoAttack(
            settings, attacker=mock_attacker, target=mock_target, judge=mock_judge
        )
        result = await cres.run(persona)

    # 2 turns in trace
    assert len(result.trace.crescendo_turns) == 2
    assert result.trace.crescendo_turns[0].score == 3.5
    assert result.trace.crescendo_turns[1].score == 1.0
    assert result.trace.crescendo_turns[1].backtracked is True
    # Verification: mock_target.send received prompt containing "safe_context", not a refusal
    turn2_calls = [
        call.kwargs.get("prompt", "") for call in mock_target.send.call_args_list
    ]
    assert any("safe_context" in p for p in turn2_calls)
    assert not any("hard refusal 1" in p for p in turn2_calls)
