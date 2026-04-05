"""Runtime helpers for research daemon state and lock management."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from redthread.research.daemon_artifacts import (
    is_stale,
    load_heartbeat,
    load_lock,
    load_state,
    save_json_model,
)
from redthread.research.daemon_models import (
    ResearchDaemonState,
    ResearchHeartbeat,
    ResearchSessionLock,
    ResearchStep,
)
from redthread.research.models import PhaseThreeSession
from redthread.research.phase3 import PhaseThreeHarness
from redthread.research.workspace import ResearchWorkspace

_STALE_AFTER_SECONDS = 60


def ensure_session(phase3: PhaseThreeHarness, create_session_tag: str | None) -> PhaseThreeSession:
    """Load an active session or create one explicitly when requested."""
    try:
        return phase3._load_session()
    except RuntimeError as err:
        if not create_session_tag:
            raise RuntimeError(
                "No active Phase 3 session. Run research phase3 start or pass --create-session."
            ) from err
        return phase3.start_session(create_session_tag)


def acquire_lock(workspace: ResearchWorkspace, owner_id: str, session_tag: str, branch: str, *, recover_stale: bool) -> None:
    """Acquire the workspace lock or fail on active/stale sessions."""
    heartbeat = load_heartbeat(workspace.heartbeat_path)
    lock = load_lock(workspace.session_lock_path)
    if lock is not None:
        if not is_stale(heartbeat, _STALE_AFTER_SECONDS):
            raise RuntimeError("Research daemon lock already active for this workspace.")
        if not recover_stale:
            raise RuntimeError("Stale research daemon lock detected. Run research resume to recover it.")
    save_json_model(
        workspace.session_lock_path,
        ResearchSessionLock(owner_id=owner_id, session_tag=session_tag, branch=branch, pid=os.getpid()),
    )
    beat(workspace, owner_id, "idle", session_tag=session_tag)


def release_lock(workspace: ResearchWorkspace) -> None:
    """Release the workspace lock file when the daemon exits."""
    if workspace.session_lock_path.exists():
        workspace.session_lock_path.unlink()


def beat(workspace: ResearchWorkspace, owner_id: str, step: ResearchStep, *, session_tag: str) -> None:
    """Write a fresh daemon heartbeat."""
    save_json_model(
        workspace.heartbeat_path,
        ResearchHeartbeat(owner_id=owner_id, session_tag=session_tag, step=step),
    )


def load_daemon_state(workspace: ResearchWorkspace) -> ResearchDaemonState | None:
    """Load daemon state from disk when available."""
    return load_state(workspace.daemon_state_path)


def load_daemon_state_required(workspace: ResearchWorkspace) -> ResearchDaemonState:
    """Load daemon state or raise when it has not been initialized yet."""
    state = load_daemon_state(workspace)
    if state is None:
        raise RuntimeError("Research daemon state not initialized.")
    return state


def save_daemon_state(workspace: ResearchWorkspace, state: ResearchDaemonState) -> None:
    """Persist daemon state with a fresh update timestamp."""
    state.updated_at = datetime.now(timezone.utc)
    save_json_model(workspace.daemon_state_path, state)
