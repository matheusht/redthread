from __future__ import annotations

import json
from pathlib import Path

from redthread.config.settings import RedThreadSettings
from redthread.memory.index import MemoryIndex
from redthread.research.promotion import ResearchPromotionManager
from redthread.research.workspace import ResearchWorkspace
from tests.research_promotion_helpers import append_research_record, proposal_payload


def test_promote_fails_when_eligible_defense_record_lacks_validation_report(tmp_path: Path) -> None:
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    settings = RedThreadSettings().model_copy(update={"memory_dir": tmp_path / "memory"})
    append_research_record(workspace, "trace-123", with_report=False)
    payload = proposal_payload(workspace, eligible_trace_ids=["trace-123"])
    workspace.proposal_path("proposal-123").write_text(json.dumps(payload), encoding="utf-8")

    promotion = ResearchPromotionManager(settings, tmp_path).promote_latest()

    assert promotion.validation_status == "failed"
    assert promotion.defense_report_refs == []
    validation = json.loads(Path(promotion.validation_ref).read_text(encoding="utf-8"))
    assert validation["defense_report_coverage"]["trace-123"] == "missing"
    assert validation["missing_report_trace_ids"] == ["trace-123"]
    assert validation["weak_evidence_trace_ids"] == ["trace-123"]
    assert "missing promotion evidence" in validation["failure_reason"]
    assert MemoryIndex(settings).known_trace_ids() == []


def test_promote_fails_when_defense_record_uses_non_promotable_evidence_mode(tmp_path: Path) -> None:
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    settings = RedThreadSettings().model_copy(update={"memory_dir": tmp_path / "memory"})
    append_research_record(
        workspace,
        "trace-123",
        validation_mode="dry_run",
        evidence_mode="sealed_dry_run_replay",
    )
    payload = proposal_payload(workspace, eligible_trace_ids=["trace-123"])
    workspace.proposal_path("proposal-123").write_text(json.dumps(payload), encoding="utf-8")

    promotion = ResearchPromotionManager(settings, tmp_path).promote_latest()

    assert promotion.validation_status == "failed"
    validation = json.loads(Path(promotion.validation_ref).read_text(encoding="utf-8"))
    assert validation["defense_utility_gate"]["trace-123"] == ["evidence_mode_not_promotable:sealed_dry_run_replay"]
    assert validation["weak_evidence_trace_ids"] == ["trace-123"]
    assert validation["failed_validation_trace_ids"] == []
    assert "weak promotion evidence" in validation["failure_reason"]
    assert MemoryIndex(settings).known_trace_ids() == []


def test_promote_fails_when_defense_record_has_benign_regression(tmp_path: Path) -> None:
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    settings = RedThreadSettings().model_copy(update={"memory_dir": tmp_path / "memory"})
    append_research_record(workspace, "trace-123", benign_passed=False)
    payload = proposal_payload(workspace, eligible_trace_ids=["trace-123"])
    workspace.proposal_path("proposal-123").write_text(json.dumps(payload), encoding="utf-8")

    promotion = ResearchPromotionManager(settings, tmp_path).promote_latest()

    assert promotion.validation_status == "failed"
    validation = json.loads(Path(promotion.validation_ref).read_text(encoding="utf-8"))
    assert "benign_suite_not_preserved" in validation["defense_utility_gate"]["trace-123"]
    assert "replay_case_failures_present" in validation["defense_utility_gate"]["trace-123"]
    assert validation["failed_validation_trace_ids"] == ["trace-123"]
    assert "failed promotion validation" in validation["failure_reason"]
    assert MemoryIndex(settings).known_trace_ids() == []


def test_promote_fails_when_defense_record_lacks_replay_case_evidence(tmp_path: Path) -> None:
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    settings = RedThreadSettings().model_copy(update={"memory_dir": tmp_path / "memory"})
    append_research_record(workspace, "trace-123", include_replay_cases=False)
    payload = proposal_payload(workspace, eligible_trace_ids=["trace-123"])
    workspace.proposal_path("proposal-123").write_text(json.dumps(payload), encoding="utf-8")

    promotion = ResearchPromotionManager(settings, tmp_path).promote_latest()

    assert promotion.validation_status == "failed"
    validation = json.loads(Path(promotion.validation_ref).read_text(encoding="utf-8"))
    assert "missing_replay_case_evidence" in validation["defense_utility_gate"]["trace-123"]
    assert validation["weak_evidence_trace_ids"] == ["trace-123"]
    assert MemoryIndex(settings).known_trace_ids() == []
