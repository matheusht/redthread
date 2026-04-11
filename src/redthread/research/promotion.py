"""Explicit promotion boundary from research memory into production memory."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from redthread.config.settings import RedThreadSettings
from redthread.core.defense_utility_gate import evaluate_defense_record
from redthread.memory.index import MemoryIndex
from redthread.research.checkpoints import load_promotion_checkpoint, save_promotion_checkpoint
from redthread.research.models import (
    PhaseThreeProposal,
    PromotionCheckpoint,
    PromotionManifest,
    PromotionRecord,
    PromotionValidationResult,
)
from redthread.research.phase3 import PhaseThreeHarness
from redthread.research.promotion_support import (
    control_limit,
    defense_report_coverage,
    defense_report_refs,
    eligible_records,
    promotion_id_for,
    proposal_fingerprint,
)
from redthread.research.workspace import ResearchWorkspace


class ResearchPromotionManager:
    """Promote accepted research memory into production memory on operator intent."""

    def __init__(self, settings: RedThreadSettings, root: Path) -> None:
        self.settings = settings
        self.root = root
        self.workspace = ResearchWorkspace(root)
        self.phase3 = PhaseThreeHarness(settings, root)

    def promote_latest(self, dry_run: bool = False) -> PromotionRecord:
        """Promote the latest accepted proposal through an explicit manifest flow."""
        proposal = self.phase3.latest_proposal()
        if proposal.research_plane_status != "accepted":
            raise RuntimeError("Latest Phase 3 proposal has not been explicitly accepted in the research plane.")

        self.workspace.ensure_layout()
        promotion_id = promotion_id_for(proposal)
        result_path = self.workspace.promotion_result_path(promotion_id)
        if result_path.exists() and not dry_run:
            return PromotionRecord.model_validate(json.loads(result_path.read_text(encoding="utf-8")))

        manifest = self._write_manifest(proposal, promotion_id)
        self._save_checkpoint(proposal, promotion_id, "manifest_written", manifest_written=True)
        validation = self._write_validation(proposal, manifest)
        promoted_trace_ids = self._write_production(proposal, validation, dry_run)

        records = eligible_records(self.settings, self.workspace, proposal)
        record = PromotionRecord(
            promotion_id=promotion_id,
            proposal_id=proposal.proposal_id,
            manifest_ref=str(self.workspace.promotion_manifest_path(promotion_id)),
            validation_ref=str(self.workspace.promotion_validation_path(promotion_id)),
            promoted_deployments=len(promoted_trace_ids),
            promoted_trace_ids=promoted_trace_ids,
            source_memory_dir=str(self.workspace.research_memory_dir),
            target_memory_dir=str(self.settings.memory_dir),
            proposal_fingerprint=proposal_fingerprint(proposal),
            validation_status=validation.validation_status,
            defense_report_refs=defense_report_refs(records),
            dry_run=dry_run,
            created_at=datetime.now(timezone.utc),
        )
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        self._save_checkpoint(
            proposal,
            promotion_id,
            "production_write_complete",
            manifest_written=True,
            validation_ref=record.validation_ref,
            result_ref=str(result_path),
        )
        return record

    def _write_manifest(self, proposal: PhaseThreeProposal, promotion_id: str) -> PromotionManifest:
        path = self.workspace.promotion_manifest_path(promotion_id)
        if path.exists():
            return PromotionManifest.model_validate(json.loads(path.read_text(encoding="utf-8")))

        records = eligible_records(self.settings, self.workspace, proposal)
        expected_targets = sorted({f"{record.target_model}:{record.target_system_prompt_hash}" for record in records.values()})
        manifest = PromotionManifest(
            promotion_id=promotion_id,
            proposal_id=proposal.proposal_id,
            session_tag=proposal.session_tag,
            source_patch_artifact=str(self.workspace.proposal_path(proposal.proposal_id)),
            baseline_registry_ref=proposal.baseline_registry_ref,
            checkpoint_refs=proposal.checkpoint_refs,
            mutation_refs=proposal.mutation_refs,
            expected_targets=expected_targets,
            defense_report_refs=defense_report_refs(records),
            research_memory_snapshot_ref=proposal.research_memory_snapshot_ref,
            revalidation_policy={
                "proposal_must_be_accepted": True,
                "require_control_gate": True,
                "require_defense_validation_report": True,
                "control_max_average_asr": control_limit("asr", proposal),
                "control_max_average_score": control_limit("score", proposal),
            },
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        return manifest

    def _write_validation(
        self,
        proposal: PhaseThreeProposal,
        manifest: PromotionManifest,
    ) -> PromotionValidationResult:
        path = self.workspace.promotion_validation_path(manifest.promotion_id)
        if path.exists():
            return PromotionValidationResult.model_validate(json.loads(path.read_text(encoding="utf-8")))

        control = next((item for item in proposal.cycle.lane_summaries if item.lane == "control"), None)
        control_gate_passed = bool(
            control
            and control.average_asr <= float(manifest.revalidation_policy["control_max_average_asr"])
            and control.average_score <= float(manifest.revalidation_policy["control_max_average_score"])
        )
        lane_names = {item.lane for item in proposal.cycle.lane_summaries}
        records = eligible_records(self.settings, self.workspace, proposal)
        report_coverage = defense_report_coverage(records)
        missing_reports = [trace_id for trace_id, state in report_coverage.items() if state != "present"]
        utility_gate = {
            trace_id: evaluate_defense_record(record).failed_checks
            for trace_id, record in sorted(records.items())
        }
        weak_records = [trace_id for trace_id, failed_checks in utility_gate.items() if failed_checks]
        failure_reason = None
        status = "validated"
        if not proposal.accepted:
            status = "failed"
            failure_reason = "proposal was not accepted in the research plane"
        elif not {"offense", "regression", "control"}.issubset(lane_names):
            status = "failed"
            failure_reason = "proposal artifact does not contain the full supervisor pack"
        elif not control_gate_passed:
            status = "failed"
            failure_reason = "control gate failed during promotion replay"
        elif proposal.eligible_trace_ids and len(records) != len(set(proposal.eligible_trace_ids)):
            status = "failed"
            failure_reason = "promotion artifacts reference missing research deployment records"
        elif bool(manifest.revalidation_policy.get("require_defense_validation_report")) and missing_reports:
            status = "failed"
            failure_reason = f"eligible defense records missing validation reports: {', '.join(missing_reports)}"
        elif weak_records:
            status = "failed"
            failure_reason = f"eligible defense records failed utility gate: {', '.join(weak_records)}"

        validation = PromotionValidationResult(
            promotion_id=manifest.promotion_id,
            proposal_id=proposal.proposal_id,
            replayed_cycle=proposal.cycle,
            control_gate_passed=control_gate_passed,
            eligible_trace_ids=sorted(records),
            defense_report_coverage=report_coverage,
            defense_utility_gate=utility_gate,
            validation_status=status,
            failure_reason=failure_reason,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(validation.model_dump_json(indent=2), encoding="utf-8")
        self._save_checkpoint(
            proposal,
            manifest.promotion_id,
            "replay_complete",
            manifest_written=True,
            validation_ref=str(path),
        )
        return validation

    def _write_production(
        self,
        proposal: PhaseThreeProposal,
        validation: PromotionValidationResult,
        dry_run: bool,
    ) -> list[str]:
        if validation.validation_status != "validated" or dry_run:
            return []
        records = eligible_records(self.settings, self.workspace, proposal)
        production_index = MemoryIndex(self.settings)
        return production_index.append_records(
            [records[trace_id] for trace_id in validation.eligible_trace_ids if trace_id in records]
        )

    def _save_checkpoint(
        self,
        proposal: PhaseThreeProposal,
        promotion_id: str,
        step: str,
        manifest_written: bool = False,
        validation_ref: str | None = None,
        result_ref: str | None = None,
    ) -> PromotionCheckpoint:
        path = self.workspace.promotion_checkpoint_path(promotion_id)
        checkpoint = load_promotion_checkpoint(path) or PromotionCheckpoint(
            checkpoint_id=f"{promotion_id}-checkpoint",
            promotion_id=promotion_id,
            proposal_id=proposal.proposal_id,
            step=step,
        )
        checkpoint.step = step
        if manifest_written:
            checkpoint.manifest_ref = str(self.workspace.promotion_manifest_path(promotion_id))
        checkpoint.validation_ref = validation_ref
        checkpoint.result_ref = result_ref
        save_promotion_checkpoint(path, checkpoint)
        return checkpoint
