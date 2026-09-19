"""Runtime helpers for research daemon state and lock management."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from redthread.research.daemon_artifacts import (
    append_failure,
    is_stale,
    load_heartbeat,
    load_lock,
    load_state,
    save_json_model,
)
from redthread.research.daemon_models import (
    DaemonStatusValue,
    ResearchDaemonState,
    ResearchDaemonStatus,
    ResearchFailureEntry,
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


def acquire_lock(
    workspace: ResearchWorkspace,
    owner_id: str,
    session_tag: str,
    branch: str,
    *,
    recover_stale: bool,
) -> None:
    """Acquire the workspace lock or fail on active/stale sessions."""
    heartbeat = load_heartbeat(workspace.heartbeat_path)
    lock = load_lock(workspace.session_lock_path)
    if lock is not None:
        if not is_stale(heartbeat, _STALE_AFTER_SECONDS):
            raise RuntimeError("Research daemon lock already active for this workspace.")
        if not recover_stale:
            raise RuntimeError(
                "Stale research daemon lock detected. Run research resume to recover it."
            )
    save_json_model(
        workspace.session_lock_path,
        ResearchSessionLock(
            owner_id=owner_id, session_tag=session_tag, branch=branch, pid=os.getpid()
        ),
    )
    beat(workspace, owner_id, "idle", session_tag=session_tag)


def release_lock(workspace: ResearchWorkspace) -> None:
    """Release the workspace lock file when the daemon exits."""
    if workspace.session_lock_path.exists():
        workspace.session_lock_path.unlink()


def beat(
    workspace: ResearchWorkspace, owner_id: str, step: ResearchStep, *, session_tag: str
) -> None:
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


def build_daemon_status(workspace: ResearchWorkspace) -> ResearchDaemonStatus:
    """Build the current daemon status snapshot."""
    state = load_daemon_state(workspace)
    heartbeat = load_heartbeat(workspace.heartbeat_path)
    lock = load_lock(workspace.session_lock_path)
    return ResearchDaemonStatus(
        session_tag=state.session_tag if state else (lock.session_tag if lock else None),
        branch=state.branch if state else (lock.branch if lock else None),
        active_lock=lock is not None and not is_stale(heartbeat, _STALE_AFTER_SECONDS),
        stale_lock=lock is not None and is_stale(heartbeat, _STALE_AFTER_SECONDS),
        last_heartbeat_at=heartbeat.updated_at if heartbeat else None,
        current_step=state.current_step if state else "idle",
        status=state.status if state else "idle",
        consecutive_failures=state.consecutive_failures if state else 0,
        cooldown_until=state.cooldown_until if state else None,
        latest_candidate_id=state.latest_candidate_id if state else None,
        latest_proposal_id=state.latest_proposal_id if state else None,
    )


def record_step_state(
    workspace: ResearchWorkspace,
    owner_id: str,
    step: ResearchStep,
    *,
    status: DaemonStatusValue = "running",
    latest_candidate_id: str | None = None,
    latest_proposal_id: str | None = None,
) -> None:
    """Update state and heartbeat after a step completes."""
    state = load_daemon_state_required(workspace)
    state.status = status
    state.current_step = step
    state.last_completed_step = step
    state.consecutive_failures = 0
    state.cooldown_until = None
    state.last_error = None
    if latest_candidate_id is not None:
        state.latest_candidate_id = latest_candidate_id
    if latest_proposal_id is not None:
        state.latest_proposal_id = latest_proposal_id
    save_daemon_state(workspace, state)
    beat(workspace, owner_id, step, session_tag=state.session_tag)


_COOLDOWN_AFTER_FAILURES = 2
_COOLDOWN_SECONDS = 5
_MAX_CONSECUTIVE_FAILURES = 3


def record_daemon_failure(
    workspace: ResearchWorkspace,
    owner_id: str,
    message: str,
) -> ResearchDaemonState:
    """Record a failure entry and transition state to cooldown or halted."""
    state = load_daemon_state_required(workspace)
    state.consecutive_failures += 1
    state.last_error = message
    if "unsafe" in message or state.consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
        state.status = "halted"
    elif state.consecutive_failures >= _COOLDOWN_AFTER_FAILURES:
        state.status = "cooldown"
        state.cooldown_until = datetime.now(timezone.utc) + timedelta(seconds=_COOLDOWN_SECONDS)
    save_daemon_state(workspace, state)
    append_failure(
        workspace.failure_log_path,
        ResearchFailureEntry(
            owner_id=owner_id,
            session_tag=state.session_tag,
            step=state.current_step,
            severity="error",
            message=message,
        ),
    )
    return state
