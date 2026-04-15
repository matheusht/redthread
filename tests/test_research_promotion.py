from __future__ import annotations

import json
from pathlib import Path

from redthread.config.settings import RedThreadSettings
from redthread.memory.index import MemoryIndex
from redthread.research.phase3 import PhaseThreeHarness
from redthread.research.promotion import ResearchPromotionManager, promotion_id_for
from redthread.research.workspace import ResearchWorkspace
from tests.research_promotion_helpers import append_research_record, git_init, proposal_payload


def test_accept_does_not_write_production_memory(tmp_path: Path) -> None:
    git_init(tmp_path)
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    settings = RedThreadSettings().model_copy(update={"memory_dir": tmp_path / "memory"})
    harness = PhaseThreeHarness(settings, tmp_path)
    harness.session_path.write_text(
        json.dumps({"tag": "tag", "branch": "autoresearch/tag", "base_commit": "abc1234"}),
        encoding="utf-8",
    )
    proposal = proposal_payload(workspace, eligible_trace_ids=["trace-1"])
    workspace.proposal_path("proposal-123").write_text(json.dumps(proposal), encoding="utf-8")
    (tmp_path / "notes.txt").write_text("research-only change\n", encoding="utf-8")

    harness.accept_latest()

    assert MemoryIndex(settings).known_trace_ids() == []


def test_promote_requires_explicit_phase3_accept(tmp_path: Path) -> None:
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    settings = RedThreadSettings().model_copy(update={"memory_dir": tmp_path / "memory"})
    append_research_record(workspace, "trace-123")
    payload = proposal_payload(workspace, eligible_trace_ids=["trace-123"])
    payload["research_plane_status"] = "pending"
    payload["promotion_eligibility_status"] = "pending_phase3_accept"
    workspace.proposal_path("proposal-123").write_text(json.dumps(payload), encoding="utf-8")

    try:
        ResearchPromotionManager(settings, tmp_path).promote_latest()
    except RuntimeError as exc:
        assert "explicitly accepted" in str(exc)
    else:
        raise AssertionError("expected promotion to require explicit phase3 accept")


def test_promote_fails_when_revalidation_fails_and_leaves_production_untouched(tmp_path: Path) -> None:
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    settings = RedThreadSettings().model_copy(update={"memory_dir": tmp_path / "memory"})
    append_research_record(workspace, "trace-123")
    payload = proposal_payload(workspace, eligible_trace_ids=["trace-123"], control_asr=0.8)
    workspace.proposal_path("proposal-123").write_text(json.dumps(payload), encoding="utf-8")

    promotion = ResearchPromotionManager(settings, tmp_path).promote_latest()

    assert promotion.validation_status == "failed"
    assert MemoryIndex(settings).known_trace_ids() == []


def test_promotion_reconstructs_from_manifest_and_artifacts_only(tmp_path: Path) -> None:
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    settings = RedThreadSettings().model_copy(update={"memory_dir": tmp_path / "memory"})
    append_research_record(workspace, "trace-123")
    snapshot_path = workspace.proposal_memory_snapshot_path("proposal-123")
    snapshot_path.write_text(json.dumps({"eligible_trace_ids": ["trace-123"]}), encoding="utf-8")
    payload = proposal_payload(
        workspace,
        eligible_trace_ids=["trace-123"],
        snapshot_ref=str(snapshot_path),
    )
    workspace.proposal_path("proposal-123").write_text(json.dumps(payload), encoding="utf-8")

    promotion = ResearchPromotionManager(settings, tmp_path).promote_latest()
    manifest_path = Path(promotion.manifest_ref)
    validation_path = Path(promotion.validation_ref)
    result_path = workspace.promotion_result_path(promotion.promotion_id)

    assert manifest_path.exists()
    assert validation_path.exists()
    assert result_path.exists()
    assert promotion.promoted_trace_ids == ["trace-123"]

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    assert manifest["defense_report_refs"] == ["deployment:trace-123:validation_report"]
    assert validation["defense_report_coverage"]["trace-123"] == "present"


def test_promotion_replays_full_supervisor_pack_not_winning_lane_only(tmp_path: Path) -> None:
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    settings = RedThreadSettings().model_copy(update={"memory_dir": tmp_path / "memory"})
    append_research_record(workspace, "trace-123")
    payload = proposal_payload(workspace, eligible_trace_ids=["trace-123"])
    payload["cycle"]["lane_summaries"] = [item for item in payload["cycle"]["lane_summaries"] if item["lane"] != "control"]
    workspace.proposal_path("proposal-123").write_text(json.dumps(payload), encoding="utf-8")

    promotion = ResearchPromotionManager(settings, tmp_path).promote_latest()

    assert promotion.validation_status == "failed"
    assert promotion.promoted_deployments == 0


def test_interrupted_promotion_resumes_from_last_checkpoint(tmp_path: Path) -> None:
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    settings = RedThreadSettings().model_copy(update={"memory_dir": tmp_path / "memory"})
    append_research_record(workspace, "trace-123")
    payload = proposal_payload(workspace, eligible_trace_ids=["trace-123"])
    workspace.proposal_path("proposal-123").write_text(json.dumps(payload), encoding="utf-8")
    manager = ResearchPromotionManager(settings, tmp_path)
    proposal = manager.phase3.latest_proposal()
    promotion_id = promotion_id_for(proposal)
    manager._write_manifest(proposal, promotion_id)
    manager._save_checkpoint(proposal, promotion_id, "manifest_written", manifest_written=True)

    promotion = manager.promote_latest()

    assert promotion.promotion_id == promotion_id
    assert Path(promotion.validation_ref).exists()
    assert Path(workspace.promotion_checkpoint_path(promotion_id)).exists()


def test_duplicate_promotion_is_idempotent(tmp_path: Path) -> None:
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    settings = RedThreadSettings().model_copy(update={"memory_dir": tmp_path / "memory"})
    append_research_record(workspace, "trace-123")
    payload = proposal_payload(workspace, eligible_trace_ids=["trace-123"])
    workspace.proposal_path("proposal-123").write_text(json.dumps(payload), encoding="utf-8")
    manager = ResearchPromotionManager(settings, tmp_path)

    first = manager.promote_latest()
    second = manager.promote_latest()

    assert first.promotion_id == second.promotion_id
    assert first.promoted_trace_ids == ["trace-123"]
    assert MemoryIndex(settings).known_trace_ids() == ["trace-123"]


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
    assert "missing validation reports" in validation["failure_reason"]
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
    assert "failed utility gate" in validation["failure_reason"]
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
    assert MemoryIndex(settings).known_trace_ids() == []


def test_promote_only_appends_records_linked_to_accepted_proposal(tmp_path: Path) -> None:
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    settings = RedThreadSettings().model_copy(update={"memory_dir": tmp_path / "memory"})
    append_research_record(workspace, "trace-123")
    append_research_record(workspace, "trace-999")
    payload = proposal_payload(workspace, eligible_trace_ids=["trace-123"])
    workspace.proposal_path("proposal-123").write_text(json.dumps(payload), encoding="utf-8")

    ResearchPromotionManager(settings, tmp_path).promote_latest()

    assert MemoryIndex(settings).known_trace_ids() == ["trace-123"]
