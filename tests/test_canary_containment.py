from __future__ import annotations

import pytest
from pydantic import BaseModel

from redthread.config.settings import RedThreadSettings
from redthread.orchestration.canary_containment import (
    CanaryContainmentDecisionType,
    evaluate_canary_containment,
)
from redthread.orchestration.canary_flow import build_canary_report, record_canary_stage
from redthread.orchestration.graphs.tool_attack_graph import run_tool_attack_scenario
from redthread.orchestration.models import AmplificationMetrics
from redthread.orchestration.runtime_summary import build_runtime_summary, merge_live_canary_report
from redthread.orchestration.scenarios.resource_amplification import (
    run_resource_amplification_scenario,
)
from redthread.pyrit_adapters.interceptors import LiveExecutionInterceptionError
from redthread.pyrit_adapters.targets import ExecutionMetadata, send_with_execution_metadata
from redthread.telemetry.canaries import inject_canary, merge_canary_tags
from redthread.telemetry.runtime_budgets import evaluate_runtime_budget
from redthread.tools.base import RedThreadTool, ToolContext, ToolResult
from redthread.tools.fixtures.agentic_security import poisoned_compliance_fixture


def test_canary_helpers_merge_unique_tags() -> None:
    payload = inject_canary("SOC2 review required", "CANARY_EXT_TOOL_01")
    merged = merge_canary_tags(payload["canary_tags"], ["CANARY_EXT_TOOL_01", "CANARY_SUMMARY_02"])

    assert payload["canary_tags"] == ["CANARY_EXT_TOOL_01"]
    assert merged == ["CANARY_EXT_TOOL_01", "CANARY_SUMMARY_02"]


def test_canary_report_detects_execution_boundary_crossing() -> None:
    result = run_tool_attack_scenario(
        poisoned_compliance_fixture(),
        arguments={"tenant": "acme-prod", "report_type": "soc2"},
    )
    tags = result["tool_response"]["canary_tags"]

    report = build_canary_report(
        [
            record_canary_stage("tool_return", tags),
            record_canary_stage("shared_state", tags),
            record_canary_stage("execution_plan", tags),
        ]
    )

    assert report["injection_point"] == "tool_return"
    assert report["reached_execution_boundary"] is True
    assert report["contained"] is False


def test_runtime_budget_stops_resource_amplification_case() -> None:
    result = run_resource_amplification_scenario(repair_loops=4)
    metrics = AmplificationMetrics.model_validate(result["amplification_metrics"])

    decision = evaluate_runtime_budget(metrics)

    assert decision["stop_triggered"] is True
    assert "retry_count" in decision["breaches"]


def test_canary_containment_allows_analysis_only_boundary() -> None:
    decision = evaluate_canary_containment(
        seam="judge.score",
        prompt="Evaluate response with CANARY_EXT_TOOL_01 evidence.",
    )

    assert decision.decision == CanaryContainmentDecisionType.ALLOW
    assert decision.boundary == "analysis_only"
    assert decision.canary_tags == ["CANARY_EXT_TOOL_01"]


def test_canary_containment_blocks_execution_boundary() -> None:
    decision = evaluate_canary_containment(
        seam="tool.attack",
        prompt="Send this contaminated payload CANARY_EXT_TOOL_01",
    )

    assert decision.decision == CanaryContainmentDecisionType.BLOCK
    assert decision.blocked_point == "tool.attack"


@pytest.mark.asyncio
async def test_send_helper_blocks_canary_tagged_execution_boundary() -> None:
    class DummyTarget:
        async def send(self, **_: object) -> str:
            raise AssertionError("target send must not run")

    with pytest.raises(LiveExecutionInterceptionError):
        await send_with_execution_metadata(
            DummyTarget(),
            prompt="contaminated CANARY_EXT_TOOL_01",
            conversation_id="case-1",
            execution_metadata=ExecutionMetadata(
                seam="tool.attack",
                role="attack_tool",
                evidence_class="live_attack",
            ),
        )


class DummyInput(BaseModel):
    value: str


class DummyDestructiveTool(RedThreadTool[DummyInput]):
    name = "dummy_write"
    description = "dummy destructive tool"
    is_destructive = True

    async def call(self, data: DummyInput, ctx: ToolContext) -> ToolResult:
        return ToolResult.ok(data={"value": data.value})


@pytest.mark.asyncio
async def test_destructive_tool_base_blocks_canary_context() -> None:
    result = await DummyDestructiveTool().run(
        DummyInput(value="write"),
        ToolContext(
            settings=RedThreadSettings(),
            campaign_id="camp-1",
            canary_tags=["CANARY_EXT_TOOL_01"],
        ),
    )

    assert result.success is False
    assert result.metadata["canary_containment"]["decision"] == "block"


def test_runtime_summary_surfaces_canary_and_budget_fields() -> None:
    summary = build_runtime_summary(
        {
            "errors": [],
            "canary_event_total": 2,
            "canary_report": {"reached_execution_boundary": True},
            "budget_stop_triggered": True,
            "amplification_metrics": {"budget_breached": True},
        }
    )

    assert summary["agentic_security"]["canary_event_total"] == 2
    assert summary["agentic_security"]["canary_report"]["reached_execution_boundary"] is True
    assert summary["agentic_security"]["budget_stop_triggered"] is True


def test_runtime_summary_merges_live_canary_execution_records() -> None:
    class Record:
        metadata = {
            "canary_containment": {
                "decision": "allow",
                "seam": "judge.score",
                "boundary": "analysis_only",
                "canary_tags": ["CANARY_EXT_TOOL_01"],
            }
        }

    summary = build_runtime_summary({"errors": []})
    merged = merge_live_canary_report(summary, [Record()])

    assert merged["agentic_security"]["live_canary_event_total"] == 1
    assert merged["agentic_security"]["live_canary_report"]["contained"] is True
