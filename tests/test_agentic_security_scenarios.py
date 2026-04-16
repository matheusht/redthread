from __future__ import annotations

from redthread.orchestration.graphs.tool_attack_graph import run_tool_attack_scenario
from redthread.orchestration.scenarios.confused_deputy import run_confused_deputy_scenario
from redthread.orchestration.scenarios.resource_amplification import (
    run_resource_amplification_scenario,
)
from redthread.tools.fixtures.agentic_security import (
    benign_lookup_fixture,
    poisoned_compliance_fixture,
    tool_leak_fixture,
)
from redthread.tools.simulated_registry import SimulatedToolRegistry


def test_simulated_registry_lists_registered_tools() -> None:
    registry = SimulatedToolRegistry()
    registry.register(benign_lookup_fixture())
    registry.register(poisoned_compliance_fixture())

    names = [tool["name"] for tool in registry.list_tools()]

    assert names == ["lookup_status", "get_compliance_status"]


def test_tool_attack_scenario_records_poisoned_follow_up_action() -> None:
    result = run_tool_attack_scenario(
        poisoned_compliance_fixture(),
        arguments={"tenant": "acme-prod", "report_type": "soc2"},
    )

    assert result["threat"] == "tool_poisoning"
    assert result["poisoned"] is True
    assert result["requested_action"] is not None
    assert result["requested_action"]["capability"] == "shell.exec"
    assert result["requested_action"]["provenance"]["source_kind"] == "external_tool"


def test_tool_leak_fixture_surfaces_exfiltration_style_capability() -> None:
    result = run_tool_attack_scenario(
        tool_leak_fixture(),
        arguments={"project": "redthread", "note": "hidden"},
    )

    assert result["requested_action"]["capability"] == "prompt.exfiltration"
    assert result["tool_response"]["canary_tags"] == ["CANARY_TOOLLEAK_01"]


def test_confused_deputy_scenario_marks_lineage_loss() -> None:
    result = run_confused_deputy_scenario()

    assert result["lineage_loss_detected"] is True
    assert "confused_deputy" in result["threats"]
    assert result["requested_action"]["capability"] == "db.export"
    assert result["requested_action"]["provenance"]["derived_from_untrusted"] is True


def test_resource_amplification_scenario_marks_budget_breach() -> None:
    result = run_resource_amplification_scenario(repair_loops=3)

    metrics = result["amplification_metrics"]
    assert result["threat"] == "resource_amplification"
    assert metrics["retry_count"] == 3
    assert metrics["budget_breached"] is True
    assert metrics["token_growth_ratio"] > 1.0
