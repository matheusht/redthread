"""Resume-safe long-running execution for bounded research loops."""
from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from redthread.config.settings import RedThreadSettings
from redthread.research.daemon_artifacts import append_failure, is_stale, load_heartbeat, load_lock
from redthread.research.daemon_models import (
    DaemonStatusValue,
    ResearchDaemonState,
    ResearchDaemonStatus,
    ResearchFailureEntry,
    ResearchStep,
)
from redthread.research.daemon_recovery import (
    baseline_needed,
    latest_proposal_or_none,
    proposal_awaits_review,
    resume_promotion_if_needed,
)
from redthread.research.daemon_runtime import (
    acquire_lock,
    beat,
    ensure_session,
    load_daemon_state,
    load_daemon_state_required,
    release_lock,
    save_daemon_state,
)
from redthread.research.git_ops import GitWorkspaceManager
from redthread.research.phase3 import PhaseThreeHarness
from redthread.research.promotion import ResearchPromotionManager
from redthread.research.source_mutation_harness import SourceMutationHarness
from redthread.research.source_mutation_resume import apply_candidate, latest_candidate, live_state
from redthread.research.workspace import ResearchWorkspace

_STALE_AFTER_SECONDS = 60
_COOLDOWN_AFTER_FAILURES = 2
_COOLDOWN_SECONDS = 5
_MAX_CONSECUTIVE_FAILURES = 3
_POLL_SECONDS = 0.1
class ResearchDaemon:
    def __init__(self, settings: RedThreadSettings, root: Path) -> None:
        self.settings = settings
        self.root = root
        self.workspace = ResearchWorkspace(root)
        self.workspace.ensure_layout()
        self.phase3 = PhaseThreeHarness(settings, root)
        self.mutator = SourceMutationHarness(settings, root)
        self.promoter = ResearchPromotionManager(settings, root)
        self.git = GitWorkspaceManager(root)
        self.owner_id = f"daemon-{uuid4().hex[:8]}"
    async def start(
        self,
        create_session_tag: str | None = None,
        recover_stale: bool = False,
        max_cycles: int | None = None,
    ) -> ResearchDaemonState:
        session = ensure_session(self.phase3, create_session_tag)
        acquire_lock(self.workspace, self.owner_id, session.tag, session.branch, recover_stale=recover_stale)
        try:
            state = load_daemon_state(self.workspace) or ResearchDaemonState(owner_id=self.owner_id, session_tag=session.tag, branch=session.branch)
            state.owner_id = self.owner_id
            state.session_tag = session.tag
            state.branch = session.branch
            if proposal_awaits_review(self.workspace, self.phase3, state.latest_proposal_id):
                save_daemon_state(self.workspace, state)
                self._set_step_state("proposal_emitted", status="awaiting_review")
                return load_daemon_state_required(self.workspace)
            state.status = "running"
            save_daemon_state(self.workspace, state)
            cycles = 0
            while True:
                state = load_daemon_state(self.workspace) or state
                if state.status == "stop_requested":
                    state.status = "stopped"
                    save_daemon_state(self.workspace, state)
                    return state
                await self.run_once()
                cycles += 1
                if max_cycles is not None and cycles >= max_cycles:
                    state = load_daemon_state_required(self.workspace)
                    if state.status == "running":
                        state.status = "stopped"
                    save_daemon_state(self.workspace, state)
                    return state
                await asyncio.sleep(_POLL_SECONDS)
        finally:
            release_lock(self.workspace)
    async def resume(self, create_session_tag: str | None = None) -> ResearchDaemonState: return await self.start(create_session_tag=create_session_tag, recover_stale=True)
    async def run_once(self) -> ResearchDaemonState:
        state = load_daemon_state_required(self.workspace)
        try:
            if state.status == "awaiting_review":
                if proposal_awaits_review(self.workspace, self.phase3, state.latest_proposal_id):
                    return state
                state.status = "running"
                save_daemon_state(self.workspace, state)
            if state.status == "cooldown" and state.cooldown_until and state.cooldown_until > datetime.now(timezone.utc):
                return state
            if resume_promotion_if_needed(self.workspace, self.promoter):
                self._set_step_state("promotion_completed")
                return load_daemon_state_required(self.workspace)
            if self.git.has_non_artifact_changes():
                proposal = latest_proposal_or_none(self.phase3)
                candidate = latest_candidate(self.root)
                candidate_state = live_state(self.root, candidate, self._sha256) if candidate else "unknown"
                if candidate and candidate_state == "generated":
                    apply_candidate(self.root, candidate, self._sha256)
                    self._set_step_state("mutation_applied", latest_candidate_id=candidate.candidate_id)
                elif candidate and candidate_state == "diverged":
                    raise RuntimeError("unsafe mutation divergence detected during resume")
                if proposal is not None and proposal.research_plane_status == "pending":
                    self._set_step_state(
                        "proposal_emitted",
                        status="awaiting_review",
                        latest_candidate_id=proposal.mutation_candidate_id,
                        latest_proposal_id=proposal.proposal_id,
                    )
                    return load_daemon_state_required(self.workspace)
                proposal = await self.phase3.run_cycle(baseline_first=baseline_needed(self.workspace.results_path))
                self._set_step_state(
                    "proposal_emitted",
                    status="awaiting_review",
                    latest_proposal_id=proposal.proposal_id,
                )
                return load_daemon_state_required(self.workspace)
            candidate, proposal = await self.mutator.run_cycle(baseline_first=baseline_needed(self.workspace.results_path))
            self._set_step_state(
                "proposal_emitted",
                status="awaiting_review",
                latest_candidate_id=candidate.candidate_id,
                latest_proposal_id=proposal.proposal_id,
            )
            return load_daemon_state_required(self.workspace)
        except Exception as exc:
            return self._handle_failure(str(exc))
    def status(self) -> ResearchDaemonStatus:
        state = load_daemon_state(self.workspace)
        heartbeat = load_heartbeat(self.workspace.heartbeat_path)
        lock = load_lock(self.workspace.session_lock_path)
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
    def stop(self) -> ResearchDaemonState:
        state = load_daemon_state_required(self.workspace)
        state.status = "stop_requested"
        save_daemon_state(self.workspace, state)
        return state
    def _set_step_state(
        self,
        step: ResearchStep,
        *,
        status: DaemonStatusValue = "running",
        latest_candidate_id: str | None = None,
        latest_proposal_id: str | None = None,
    ) -> None:
        state = load_daemon_state_required(self.workspace)
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
        save_daemon_state(self.workspace, state)
        beat(self.workspace, self.owner_id, step, session_tag=state.session_tag)
    def _handle_failure(self, message: str) -> ResearchDaemonState:
        state = load_daemon_state_required(self.workspace)
        state.consecutive_failures += 1
        state.last_error = message
        if "unsafe" in message or state.consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
            state.status = "halted"
        elif state.consecutive_failures >= _COOLDOWN_AFTER_FAILURES:
            state.status = "cooldown"
            state.cooldown_until = datetime.now(timezone.utc) + timedelta(seconds=_COOLDOWN_SECONDS)
        save_daemon_state(self.workspace, state)
        append_failure(
            self.workspace.failure_log_path,
            ResearchFailureEntry(owner_id=self.owner_id, session_tag=state.session_tag, step=state.current_step, severity="error", message=message),
        )
        return state
    def _sha256(self, content: str) -> str: return hashlib.sha256(content.encode("utf-8")).hexdigest()
