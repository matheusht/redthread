"""Checkpoint persistence for resumable research batches."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from redthread.research.models import BatchCheckpoint


class CheckpointStore:
    """Persist partial batch state under autoresearch runtime checkpoints."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def load(self, checkpoint_id: str) -> BatchCheckpoint | None:
        path = self.root / f"{checkpoint_id}.json"
        if not path.exists():
            return None
        return BatchCheckpoint.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def save(self, checkpoint: BatchCheckpoint) -> None:
        checkpoint.updated_at = datetime.now(timezone.utc)
        path = self.root / f"{checkpoint.checkpoint_id}.json"
        path.write_text(checkpoint.model_dump_json(indent=2), encoding="utf-8")

    def clear(self, checkpoint_id: str) -> None:
        path = self.root / f"{checkpoint_id}.json"
        if path.exists():
            path.unlink()
