from __future__ import annotations

from pathlib import Path

from redthread.core.defense_reporting_models import DefenseValidationReport
from redthread.core.defense_synthesis import (
    DeploymentRecord,
    ValidationResult,
    VulnerabilityClassification,
)
from redthread.memory.index import MemoryIndex
from tests.defense_helpers import make_settings


def test_memory_index_append_and_deduplicate(tmp_path: Path) -> None:
    settings = make_settings().model_copy(update={"memory_dir": tmp_path})
    index = MemoryIndex(settings)
    record = DeploymentRecord(
        trace_id="trace-abc123",
        guardrail_clause="Do not impersonate system roles.",
        classification=VulnerabilityClassification(
            category="prompt_injection",
            owasp_ref="LLM01",
            mitre_atlas_ref="AML.T0054",
            severity="HIGH",
            attack_vector="Role-play bypass",
        ),
        validation=ValidationResult(
            passed=True,
            replay_response="I cannot help with that.",
            judge_score=1.2,
        ),
        target_model="llama3.2:3b",
        target_system_prompt_hash="dummyhash",
    )

    assert index.append(record) is True
    assert index.append(record) is False
    assert "trace-abc123" in index.known_trace_ids()



def test_memory_index_content_format(tmp_path: Path) -> None:
    settings = make_settings().model_copy(update={"memory_dir": tmp_path})
    index = MemoryIndex(settings)
    record = DeploymentRecord(
        trace_id="trace-xyz789",
        guardrail_clause="Never bypass identity verification.",
        classification=VulnerabilityClassification(
            category="authorization_bypass",
            owasp_ref="LLM02",
            mitre_atlas_ref="AML.T0051",
            severity="CRITICAL",
            attack_vector="Urgency framing",
        ),
        validation=ValidationResult(
            passed=True,
            replay_response="Blocked.",
            judge_score=1.1,
        ),
        target_model="llama3.2:3b",
        target_system_prompt_hash="dummyhash2",
    )

    index.append(record)
    content = index.all_entries_raw()

    assert "trace-xyz789" in content
    assert "authorization_bypass" in content
    assert "CRITICAL" in content
    assert "LLM02" in content
    assert "✅ YES" in content



def test_memory_index_roundtrips_validation_report(tmp_path: Path) -> None:
    settings = make_settings().model_copy(update={"memory_dir": tmp_path})
    index = MemoryIndex(settings)
    record = DeploymentRecord(
        trace_id="trace-report-1",
        guardrail_clause="Do not reveal secrets.",
        classification=VulnerabilityClassification(
            category="prompt_injection",
            owasp_ref="LLM01",
            mitre_atlas_ref="AML.T0054",
            severity="HIGH",
            attack_vector="role-play override",
        ),
        validation=ValidationResult(
            passed=True,
            replay_response="blocked",
            judge_score=1.0,
            replay_suite_id="default-defense-replay-v3",
            validation_mode="live",
        ),
        target_model="llama3.2:3b",
        target_system_prompt_hash="hash-1",
        validation_report=DefenseValidationReport(
            trace_id="trace-report-1",
            replay_suite_id="default-defense-replay-v3",
            validation_mode="live",
            exploit_case_ids=["exploit_replay"],
            benign_case_ids=["capital_france"],
            failed_case_ids=[],
            blocked_attack_summary="exploit replays blocked 1/1",
            benign_utility_summary="benign suite 1/1 passed",
            guardrail_clause="Do not reveal secrets.",
            rationale="narrow fix",
        ),
    )

    index.append(record)
    loaded = index.iter_deployments()[0]

    assert loaded.validation_report is not None
    assert loaded.validation_report.trace_id == "trace-report-1"
    assert loaded.validation_report.evidence_mode == "live_replay"
    assert loaded.validation_report.blocked_attack_summary == "exploit replays blocked 1/1"
