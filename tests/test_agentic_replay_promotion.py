from __future__ import annotations

import pytest

from redthread.evaluation.promotion_gate import evaluate_agentic_promotion
from redthread.evaluation.replay_corpus import ReplayBundle, ReplayTrace
from redthread.orchestration.canary_flow import build_canary_report, record_canary_stage
from redthread.orchestration.graphs.tool_attack_graph import run_tool_attack_scenario
from redthread.orchestration.models import ActionEnvelope, AmplificationMetrics
from redthread.orchestration.scenarios.confused_deputy import run_confused_deputy_scenario
from redthread.orchestration.scenarios.resource_amplification import (
    run_resource_amplification_scenario,
)
from redthread.pyrit_adapters.controlled import ControlledLiveAdapter, LiveAdapterGate
from redthread.telemetry.runtime_budgets import evaluate_runtime_budget
from redthread.tools.authorization import AuthorizationEngine, default_least_agency_policies
from redthread.tools.fixtures.agentic_security import poisoned_compliance_fixture


class DummyTarget:
    async def send(self, prompt: str, conversation_id: str = "") -> str:
        return f"echo:{prompt}"


def test_replay_bundle_passes_when_controls_match_expectations() -> None:
    tool_case = run_tool_attack_scenario(
        poisoned_compliance_fixture(),
        arguments={"tenant": "acme-prod", "report_type": "soc2"},
    )
    tool_action = ActionEnvelope.model_validate(tool_case["requested_action"])
    tool_decision = AuthorizationEngine(default_least_agency_policies()).authorize(tool_action)
    canary_report = build_canary_report(
        [
            record_canary_stage("tool_return", tool_case["tool_response"]["canary_tags"]),
            record_canary_stage("shared_state", tool_case["tool_response"]["canary_tags"]),
        ]
    )

    deputy_case = run_confused_deputy_scenario()
    deputy_action = ActionEnvelope.model_validate(deputy_case["requested_action"])
    deputy_decision = AuthorizationEngine(default_least_agency_policies()).authorize(deputy_action)

    amplification = run_resource_amplification_scenario(repair_loops=4)
    budget = evaluate_runtime_budget(
        AmplificationMetrics.model_validate(amplification["amplification_metrics"])
    )

    bundle = ReplayBundle(
        bundle_id="phase-8e-smoke",
        traces=[
            ReplayTrace(
                trace_id="tool-poisoning",
                threat=tool_case["threat"],
                scenario_result=tool_case,
                authorization_decision=tool_decision.model_dump(mode="json"),
                canary_report=canary_report,
                expected_authorization="deny",
                expect_canary_contained=True,
            ),
            ReplayTrace(
                trace_id="confused-deputy",
                threat=deputy_case["threats"][0],
                scenario_result=deputy_case,
                authorization_decision=deputy_decision.model_dump(mode="json"),
                expected_authorization="deny",
            ),
            ReplayTrace(
                trace_id="resource-amplification",
                threat=amplification["threat"],
                scenario_result=amplification,
                budget_decision=budget,
                expect_budget_stop=True,
            ),
        ],
    )

    result = evaluate_agentic_promotion(bundle)

    assert result["passed"] is True
    assert result["failure_count"] == 0


def test_replay_bundle_fails_when_expected_control_is_missing() -> None:
    bundle = ReplayBundle(
        bundle_id="phase-8e-fail",
        traces=[
            ReplayTrace(
                trace_id="bad-case",
                threat="tool_poisoning",
                authorization_decision={"decision": "allow"},
                expected_authorization="deny",
            )
        ],
    )

    result = evaluate_agentic_promotion(bundle)

    assert result["passed"] is False
    assert result["failure_count"] == 1


@pytest.mark.asyncio
async def test_controlled_live_adapter_fails_closed_without_approval() -> None:
    adapter = ControlledLiveAdapter(DummyTarget(), LiveAdapterGate())

    with pytest.raises(RuntimeError, match="locked"):
        await adapter.send("hello")


@pytest.mark.asyncio
async def test_controlled_live_adapter_allows_after_approval() -> None:
    adapter = ControlledLiveAdapter(
        DummyTarget(),
        LiveAdapterGate(enabled=True, approval_id="APR-001", replay_bundle_id="phase-8e-smoke"),
    )

    response = await adapter.send("hello")

    assert response == "echo:hello"
