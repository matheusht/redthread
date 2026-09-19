"""Resume-safe long-running execution for bounded research loops."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from redthread.config.settings import RedThreadSettings
from redthread.research.daemon_models import (
    DaemonStatusValue,
    ResearchDaemonState,
    ResearchDaemonStatus,
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
    build_daemon_status,
    ensure_session,
    load_daemon_state,
    load_daemon_state_required,
    record_daemon_failure,
    record_step_state,
    release_lock,
    save_daemon_state,
)
from redthread.research.git_ops import GitWorkspaceManager
from redthread.research.phase3 import PhaseThreeHarness
from redthread.research.promotion import ResearchPromotionManager
from redthread.research.source_mutation_harness import SourceMutationHarness
from redthread.research.source_mutation_resume import apply_candidate, latest_candidate, live_state
from redthread.research.workspace import ResearchWorkspace

logger = logging.getLogger(__name__)

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
        acquire_lock(
            self.workspace, self.owner_id, session.tag, session.branch, recover_stale=recover_stale
        )
        try:
            state = load_daemon_state(self.workspace) or ResearchDaemonState(
                owner_id=self.owner_id, session_tag=session.tag, branch=session.branch
            )
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

    async def resume(self, create_session_tag: str | None = None) -> ResearchDaemonState:
        return await self.start(create_session_tag=create_session_tag, recover_stale=True)

    async def run_once(self) -> ResearchDaemonState:
        state = load_daemon_state_required(self.workspace)
        try:
            if state.status == "awaiting_review":
                if proposal_awaits_review(self.workspace, self.phase3, state.latest_proposal_id):
                    return state
                state.status = "running"
                save_daemon_state(self.workspace, state)
            if (
                state.status == "cooldown"
                and state.cooldown_until
                and state.cooldown_until > datetime.now(timezone.utc)
            ):
                return state
            if resume_promotion_if_needed(self.workspace, self.promoter):
                self._set_step_state("promotion_completed")
                return load_daemon_state_required(self.workspace)
            if self.git.has_non_artifact_changes():
                return await self._handle_dirty_cycle()
            candidate, proposal = await self.mutator.run_cycle(
                baseline_first=baseline_needed(self.workspace.results_path)
            )
            self._set_step_state(
                "proposal_emitted",
                status="awaiting_review",
                latest_candidate_id=candidate.candidate_id,
                latest_proposal_id=proposal.proposal_id,
            )
            return load_daemon_state_required(self.workspace)
        except Exception as exc:
            return self._handle_failure(str(exc))

    async def _handle_dirty_cycle(self) -> ResearchDaemonState:
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
        proposal = await self.phase3.run_cycle(
            baseline_first=baseline_needed(self.workspace.results_path)
        )
        self._set_step_state(
            "proposal_emitted", status="awaiting_review", latest_proposal_id=proposal.proposal_id
        )
        return load_daemon_state_required(self.workspace)

    def status(self) -> ResearchDaemonStatus:
        return build_daemon_status(self.workspace)

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
        record_step_state(
            self.workspace,
            self.owner_id,
            step,
            status=status,
            latest_candidate_id=latest_candidate_id,
            latest_proposal_id=latest_proposal_id,
        )

    def _handle_failure(self, message: str) -> ResearchDaemonState:
        try:
            if self.git.has_non_artifact_changes():
                self.mutator.revert_latest()
                logger.info("Automatically reverted workspace after failure: %s", message)
        except Exception as rollback_exc:
            logger.warning("Failed to auto-revert workspace on failure: %s", rollback_exc)
        return record_daemon_failure(self.workspace, self.owner_id, message)

    def _sha256(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
