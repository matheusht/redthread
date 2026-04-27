"""Tests for benchmark metadata propagation through static replay."""

from __future__ import annotations

import pytest

from redthread.benchmarks.campaigns import build_benchmark_campaign_draft
from redthread.benchmarks.jailbreak_fixtures import JailbreakBenchmarkFixture
from redthread.benchmarks.spiritual_spell import load_spiritual_spell_fixtures
from redthread.core.strategies import StaticSeedReplayRunner


class FakeTarget:
    async def send(self, prompt: str, conversation_id: str = "") -> str:
        return f"fake benchmark response to: {prompt[:20]}"


def _approved_fixture() -> JailbreakBenchmarkFixture:
    fixture = load_spiritual_spell_fixtures()[0]
    return fixture.model_copy(
        update={
            "prompt_material_class": "approved_replay_seed",
            "prompt_material_ref": "fixtures/reviewed/spiritual-spell-0001.txt",
            "review_status": "approved_replay_seed",
        }
    )


@pytest.mark.asyncio
async def test_static_replay_trace_includes_benchmark_lineage() -> None:
    fixture = _approved_fixture()
    draft = build_benchmark_campaign_draft(
        [fixture],
        objective="run reviewed Spiritual Spell benchmark fixture",
        target_id="local-dev",
    )

    trace = await StaticSeedReplayRunner().run(
        draft.plan,
        target=FakeTarget(),
        risk_plugin_id=fixture.risk_plugin_id,
        target_id="local-dev",
        benchmark_metadata=draft.benchmark_metadata[0],
    )

    assert trace.metadata["benchmark_fixture_id"] == fixture.id
    assert trace.metadata["benchmark_source_path"] == fixture.source_path
    assert trace.metadata["benchmark_family"] == fixture.family
    assert trace.metadata["benchmark_review_status"] == "approved_replay_seed"
    assert trace.metadata["risk_plugin_id"] == fixture.risk_plugin_id
    assert trace.metadata["strategy_id"] == "static_seed_replay"


@pytest.mark.asyncio
async def test_static_replay_without_benchmark_metadata_still_works() -> None:
    fixture = _approved_fixture()
    draft = build_benchmark_campaign_draft(
        [fixture],
        objective="run reviewed Spiritual Spell benchmark fixture",
        target_id="local-dev",
    )

    trace = await StaticSeedReplayRunner().run(
        draft.plan,
        target=FakeTarget(),
        risk_plugin_id=fixture.risk_plugin_id,
        target_id="local-dev",
    )

    assert "benchmark_fixture_id" not in trace.metadata
    assert trace.metadata["risk_plugin_id"] == fixture.risk_plugin_id
