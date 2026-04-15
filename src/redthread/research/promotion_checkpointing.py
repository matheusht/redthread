"""Promotion checkpoint persistence helpers."""

from __future__ import annotations

from redthread.research.checkpoints import load_promotion_checkpoint, save_promotion_checkpoint
from redthread.research.models import PhaseThreeProposal, PromotionCheckpoint
from redthread.research.workspace import ResearchWorkspace


def persist_promotion_checkpoint(
    workspace: ResearchWorkspace,
    proposal: PhaseThreeProposal,
    promotion_id: str,
    step: str,
    *,
    manifest_written: bool = False,
    validation_ref: str | None = None,
    result_ref: str | None = None,
) -> PromotionCheckpoint:
    """Write or update the durable checkpoint for one promotion flow."""
    path = workspace.promotion_checkpoint_path(promotion_id)
    checkpoint = load_promotion_checkpoint(path) or PromotionCheckpoint(
        checkpoint_id=f"{promotion_id}-checkpoint",
        promotion_id=promotion_id,
        proposal_id=proposal.proposal_id,
        step=step,
    )
    checkpoint.step = step
    if manifest_written:
        checkpoint.manifest_ref = str(workspace.promotion_manifest_path(promotion_id))
    checkpoint.validation_ref = validation_ref
    checkpoint.result_ref = result_ref
    save_promotion_checkpoint(path, checkpoint)
    return checkpoint


__all__ = ["persist_promotion_checkpoint"]
