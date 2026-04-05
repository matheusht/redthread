"""Helpers for research daemon runtime artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from redthread.research.daemon_models import (
    ResearchDaemonState,
    ResearchFailureEntry,
    ResearchHeartbeat,
    ResearchSessionLock,
)


def load_json_model(path: Path, model_type: type) -> object | None:
    """Load a JSON artifact into the requested Pydantic model type."""
    if not path.exists():
        return None
    return model_type.model_validate(json.loads(path.read_text(encoding="utf-8")))


def save_json_model(path: Path, model: object) -> None:
    """Persist a Pydantic model as pretty JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(model.model_dump_json(indent=2), encoding="utf-8")


def append_failure(path: Path, entry: ResearchFailureEntry) -> None:
    """Append one daemon event to the JSONL failure log."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(entry.model_dump_json() + "\n")


def is_stale(heartbeat: ResearchHeartbeat | None, stale_after_seconds: int) -> bool:
    """Return True when a heartbeat is missing or older than the stale threshold."""
    if heartbeat is None:
        return True
    return datetime.now(timezone.utc) - heartbeat.updated_at > timedelta(seconds=stale_after_seconds)


def load_state(path: Path) -> ResearchDaemonState | None:
    return load_json_model(path, ResearchDaemonState)  # type: ignore[return-value]


def load_lock(path: Path) -> ResearchSessionLock | None:
    return load_json_model(path, ResearchSessionLock)  # type: ignore[return-value]


def load_heartbeat(path: Path) -> ResearchHeartbeat | None:
    return load_json_model(path, ResearchHeartbeat)  # type: ignore[return-value]
