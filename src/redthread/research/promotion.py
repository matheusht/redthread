"""Explicit promotion boundary from research memory into production memory."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from redthread.config.settings import RedThreadSettings
from redthread.core.defense_synthesis import DeploymentRecord
from redthread.memory.index import MemoryIndex
from redthread.research.models import PromotionRecord
from redthread.research.phase3 import PhaseThreeHarness
from redthread.research.workspace import ResearchWorkspace


class ResearchPromotionManager:
    """Promote accepted research memory into production memory on operator intent."""

    def __init__(self, settings: RedThreadSettings, root: Path) -> None:
        self.settings = settings
        self.workspace = ResearchWorkspace(root)
        self.phase3 = PhaseThreeHarness(settings, root)

    def promote_latest(self) -> PromotionRecord:
        """Replay accepted research deployment records into production MEMORY.md."""
        proposal = self.phase3.latest_proposal()
        if proposal.recommended_action != "accept":
            raise RuntimeError("Latest Phase 3 proposal is not accepted.")

        self.workspace.ensure_layout()
        source_index = MemoryIndex(self.workspace.research_settings(self.settings))
        production_index = MemoryIndex(self.settings)
        promoted = 0

        for record in source_index.iter_deployments():
            if record.validation.passed and production_index.append(record):
                promoted += 1

        promotion = PromotionRecord(
            promotion_id=f"promotion-{uuid4().hex[:8]}",
            proposal_id=proposal.proposal_id,
            promoted_deployments=promoted,
            source_memory_dir=str(self.workspace.research_memory_dir),
            target_memory_dir=str(self.settings.memory_dir),
            created_at=datetime.now(timezone.utc),
        )
        path = self.workspace.promotions_dir / f"{promotion.promotion_id}.json"
        path.write_text(promotion.model_dump_json(indent=2), encoding="utf-8")
        return promotion
