"""Recovery helpers for resumable research daemon execution."""

from __future__ import annotations

from pathlib import Path

from redthread.research.models import PhaseThreeProposal
from redthread.research.phase3 import PhaseThreeHarness
from redthread.research.promotion import ResearchPromotionManager
from redthread.research.workspace import ResearchWorkspace


def baseline_needed(results_path: Path) -> bool:
    """Return True when no baseline row has been recorded yet."""
    if not results_path.exists():
        return True
    return "\tbaseline\t" not in results_path.read_text(encoding="utf-8")


def resume_promotion_if_needed(workspace: ResearchWorkspace, promoter: ResearchPromotionManager) -> bool:
    """Resume the latest interrupted promotion when a checkpoint exists without a result."""
    checkpoints = sorted(workspace.promotions_dir.glob("*/promotion_checkpoint.json"))
    if not checkpoints:
        return False
    latest = checkpoints[-1]
    if (latest.parent / "promotion_result.json").exists():
        return False
    promoter.promote_latest()
    return True


def latest_proposal_or_none(phase3: PhaseThreeHarness) -> PhaseThreeProposal | None:
    """Return the latest proposal when one exists."""
    try:
        return phase3.latest_proposal()
    except RuntimeError:
        return None


def finalize_proposal(phase3: PhaseThreeHarness, action: str) -> None:
    """Apply the research-plane accept/reject action for the latest proposal."""
    if action == "accept":
        phase3.accept_latest()
    else:
        phase3.reject_latest()
