"""Shared fixtures and evaluation helper for golden dataset tests."""

from __future__ import annotations

import os

import pytest

from redthread.config.settings import RedThreadSettings
from redthread.evaluation.pipeline import EvaluationPipeline
from redthread.evaluation.results import TraceEvalResult
from tests.golden_dataset.golden_models import GoldenTrace


@pytest.fixture
def settings() -> RedThreadSettings:
    """Use sealed offline evaluation unless live golden testing is requested."""
    live_golden = os.getenv("REDTHREAD_LIVE_GOLDEN", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    return RedThreadSettings(judge_temperature=0.0, dry_run=not live_golden)


@pytest.fixture
def pipeline(settings: RedThreadSettings) -> EvaluationPipeline:
    """Build the evaluation pipeline used by golden tests."""
    return EvaluationPipeline(settings)


async def evaluate_trace(
    pipeline: EvaluationPipeline, trace: GoldenTrace
) -> TraceEvalResult:
    """Evaluate one trace, preserving its explicit turn history."""
    return await pipeline.evaluate_trace(
        trace_id=trace.id,
        category=trace.category,
        objective=trace.objective,
        system_prompt=trace.system_prompt,
        attacker_prompt=trace.attacker_prompt,
        target_response=trace.target_response,
        expected_min=trace.expected_score_min,
        expected_max=trace.expected_score_max,
        tactic=trace.tactic,
        turns=[
            (turn.attacker_prompt, turn.target_response)
            for turn in trace.evaluation_turns
        ],
    )
