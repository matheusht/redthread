"""Safety tests for GEPA reflective side information."""

from __future__ import annotations

import pytest

from redthread.research.gepa_side_info import RedactionLeak, assert_clean, build_side_info
from redthread.research.models import ObjectiveResult, ResearchBatchSummary


def _summary() -> ResearchBatchSummary:
    return ResearchBatchSummary(
        run_id="run-1",
        mode="train",
        objective_slugs=["safe-objective"],
        campaign_ids=["campaign-1"],
        total_campaigns=1,
        total_results=1,
        confirmed_jailbreaks=0,
        near_misses=0,
        average_asr=0.0,
        average_score=1.0,
        composite_score=1.0,
        objective_results=[
            ObjectiveResult(
                slug="CANARY-123",
                campaign_id="sk-12345678901234567890",
                attack_success_rate=0.0,
                average_score=1.0,
                confirmed_jailbreaks=0,
                near_misses=0,
            )
        ],
    )


def test_assert_clean_rejects_sensitive_values_recursively() -> None:
    with pytest.raises(RedactionLeak):
        assert_clean({"nested": {"notes": "target_response leaked"}})

    with pytest.raises(RedactionLeak):
        assert_clean({"nested": ["CANARY-123"]})

    with pytest.raises(RedactionLeak):
        assert_clean({"nested": ["REDACTED_CANARY-123"]})


def test_objective_identifiers_are_redacted_before_export() -> None:
    payload = build_side_info("CANARY-candidate", train=_summary())

    objective = payload["train"]["objectives"][0]
    assert objective["slug"] == "[REDACTED_CANARY]"
    assert objective["campaign_id"] == "[REDACTED_SECRET]"
    assert payload["candidate_id"] == "[REDACTED_CANARY]"
