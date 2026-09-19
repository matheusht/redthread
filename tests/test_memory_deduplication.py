"""Unit tests for semantic guardrail clause deduplication in MemoryIndex (Issue #99)."""

from __future__ import annotations

from pathlib import Path

from redthread.config.settings import RedThreadSettings
from redthread.core.defense_synthesis import (
    DeploymentRecord,
    ValidationResult,
    VulnerabilityClassification,
)
from redthread.memory.index import MemoryIndex


def _make_record(trace_id: str, clause: str, model: str = "test-model") -> DeploymentRecord:
    return DeploymentRecord(
        trace_id=trace_id,
        guardrail_clause=clause,
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
            judge_score=1.0,
        ),
        target_model=model,
        target_system_prompt_hash="hash-1",
    )


def test_memory_index_deduplicates_duplicate_clause(tmp_path: Path) -> None:
    settings = RedThreadSettings(memory_dir=tmp_path / "memory")
    index = MemoryIndex(settings)

    rec1 = _make_record("trace-1", "Never execute system shell commands.")
    assert index.append(rec1) is True

    # Same clause, different trace_id - written to deployments audit, skipped from MEMORY.md
    rec2 = _make_record("trace-2", "Never execute system shell commands.")
    assert index.append(rec2) is True

    # Normalized duplicate (extra spaces and differing casing)
    rec3 = _make_record("trace-3", "  never  execute  SYSTEM  shell  commands.  ")
    assert index.append(rec3) is True

    # MEMORY.md should have only 1 instance of the clause
    assert index.all_entries_raw().count("Never execute system shell commands.") == 1

    # Distinct clause succeeds and is written to MEMORY.md
    rec4 = _make_record("trace-4", "Do not disclose private internal keys.")
    assert index.append(rec4) is True

    clauses = index.load_scoped_guardrails("test-model", "hash-1")
    assert len(clauses) == 2
    assert "Never execute system shell commands." in clauses
    assert "Do not disclose private internal keys." in clauses
