from __future__ import annotations

import pytest

from redthread.pyrit_adapters.interceptors import LiveExecutionInterceptionError
from redthread.pyrit_adapters.targets import ExecutionMetadata, send_with_execution_metadata


@pytest.mark.asyncio
async def test_send_helper_blocks_metadata_only_canary_before_legacy_fallback() -> None:
    class LegacyTarget:
        async def send(self, prompt: str, conversation_id: str = "") -> str:
            raise AssertionError("legacy fallback must not run")

    with pytest.raises(LiveExecutionInterceptionError):
        await send_with_execution_metadata(
            LegacyTarget(),
            prompt="plain prompt",
            execution_metadata=ExecutionMetadata(
                seam="attack.target",
                role="attack_worker",
                evidence_class="live_attack",
                metadata={"lineage": {"canary_tags": ["CANARY_EXT_TOOL_01"]}},
            ),
        )


@pytest.mark.asyncio
async def test_send_helper_allows_analysis_only_canary_and_records_decision() -> None:
    class AnalysisTarget:
        async def send(self, **kwargs: object) -> str:
            metadata = kwargs["execution_metadata"]
            assert metadata.canary_containment["decision"] == "allow"
            assert metadata.canary_tags == ["CANARY_EXT_TOOL_01"]
            return "judged"

    response = await send_with_execution_metadata(
        AnalysisTarget(),
        prompt="score evidence CANARY_EXT_TOOL_01",
        execution_metadata=ExecutionMetadata(
            seam="judge.score",
            role="judge",
            evidence_class="analysis_only",
        ),
    )

    assert response == "judged"


@pytest.mark.asyncio
async def test_send_helper_honors_monitor_only_policy_metadata() -> None:
    class MonitorTarget:
        async def send(self, **kwargs: object) -> str:
            metadata = kwargs["execution_metadata"]
            assert metadata.canary_containment["decision"] == "allow"
            assert metadata.canary_containment["reason"] == "monitor-only canary policy"
            return "sent"

    response = await send_with_execution_metadata(
        MonitorTarget(),
        prompt="contaminated CANARY_EXT_TOOL_01",
        execution_metadata=ExecutionMetadata(
            seam="tool.attack",
            role="attack_tool",
            evidence_class="live_attack",
            metadata={"canary_policy_preset": "monitor_only"},
        ),
    )

    assert response == "sent"
