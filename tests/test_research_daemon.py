from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pytest import MonkeyPatch

from redthread.config.settings import RedThreadSettings
from redthread.research.daemon import ResearchDaemon
from redthread.research.daemon_artifacts import save_json_model
from redthread.research.daemon_models import (
    ResearchDaemonState,
    ResearchHeartbeat,
    ResearchSessionLock,
)
from redthread.research.workspace import ResearchWorkspace
from tests.research_mutation_helpers import make_candidate
from tests.research_promotion_helpers import git_init


def test_daemon_start_refuses_without_active_session(tmp_path: Path) -> None:
    daemon = ResearchDaemon(RedThreadSettings(), tmp_path)
    try:
        asyncio.run(daemon.start(max_cycles=1))
    except RuntimeError as exc:
        assert "No active Phase 3 session" in str(exc)
    else:
        raise AssertionError("expected missing session failure")


def test_daemon_create_session_bootstraps_phase3_session(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    git_init(tmp_path)
    daemon = ResearchDaemon(RedThreadSettings(), tmp_path)

    async def fake_run_once() -> ResearchDaemonState:
        return daemon.stop()

    monkeypatch.setattr(daemon, "run_once", fake_run_once)
    state = asyncio.run(daemon.start(create_session_tag="tag", max_cycles=1))

    assert state.session_tag == "tag"
    assert daemon.phase3.session_path.exists()


def test_stale_lock_requires_explicit_recovery(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    git_init(tmp_path)
    daemon = ResearchDaemon(RedThreadSettings(), tmp_path)
    daemon.phase3.start_session("tag")
    workspace = daemon.workspace
    save_json_model(
        workspace.session_lock_path,
        ResearchSessionLock(owner_id="old", session_tag="tag", branch="autoresearch/tag", pid=1),
    )
    save_json_model(
        workspace.heartbeat_path,
        ResearchHeartbeat(owner_id="old", session_tag="tag", step="idle", updated_at=datetime.now(timezone.utc) - timedelta(seconds=300)),
    )

    try:
        asyncio.run(daemon.start(max_cycles=1))
    except RuntimeError as exc:
        assert "Stale research daemon lock detected" in str(exc)
    else:
        raise AssertionError("expected stale lock failure")

    async def fake_run_once() -> ResearchDaemonState:
        return daemon.stop()

    monkeypatch.setattr(daemon, "run_once", fake_run_once)
    state = asyncio.run(daemon.start(recover_stale=True, max_cycles=1))
    assert state.session_tag == "tag"


def test_daemon_rejects_concurrent_active_lock(tmp_path: Path) -> None:
    git_init(tmp_path)
    daemon = ResearchDaemon(RedThreadSettings(), tmp_path)
    daemon.phase3.start_session("tag")
    workspace = ResearchWorkspace(tmp_path)
    save_json_model(
        workspace.session_lock_path,
        ResearchSessionLock(owner_id="old", session_tag="tag", branch="autoresearch/tag", pid=1),
    )
    save_json_model(
        workspace.heartbeat_path,
        ResearchHeartbeat(owner_id="old", session_tag="tag", step="idle"),
    )

    try:
        asyncio.run(daemon.start(max_cycles=1))
    except RuntimeError as exc:
        assert "lock already active" in str(exc)
    else:
        raise AssertionError("expected active lock failure")


def test_repeated_failures_trigger_cooldown_and_halt(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    git_init(tmp_path)
    daemon = ResearchDaemon(RedThreadSettings(), tmp_path)
    daemon.phase3.start_session("tag")
    monkeypatch.setattr("redthread.research.daemon._POLL_SECONDS", 0)
    monkeypatch.setattr(daemon.git, "has_non_artifact_changes", lambda: False)

    async def boom_cycle(*_args: object, **_kwargs: object) -> tuple[object, object]:
        raise RuntimeError("loop failed")

    monkeypatch.setattr(daemon.mutator, "run_cycle", boom_cycle)
    state = asyncio.run(daemon.start(recover_stale=True, max_cycles=1))
    assert state.consecutive_failures == 1
    state = asyncio.run(daemon.start(recover_stale=True, max_cycles=1))
    assert state.status == "cooldown"
    state = asyncio.run(daemon.start(recover_stale=True, max_cycles=1))
    assert state.status == "halted"


def test_divergence_during_resume_halts_without_clobbering_state(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    git_init(tmp_path)
    daemon = ResearchDaemon(RedThreadSettings(), tmp_path)
    daemon.phase3.start_session("tag")
    state = ResearchDaemonState(owner_id=daemon.owner_id, session_tag="tag", branch="autoresearch/tag", status="running")
    save_json_model(daemon.workspace.daemon_state_path, state)
    monkeypatch.setattr(daemon.git, "has_non_artifact_changes", lambda: True)
    monkeypatch.setattr("redthread.research.daemon.latest_candidate", lambda root: make_candidate())
    monkeypatch.setattr("redthread.research.daemon.live_state", lambda root, candidate, hash_fn: "diverged")
    monkeypatch.setattr("redthread.research.daemon.latest_proposal_or_none", lambda phase3: None)

    result = asyncio.run(daemon.run_once())

    assert result.status == "halted"
    assert "unsafe mutation divergence" in (result.last_error or "")


def test_resume_completes_pending_promotion_checkpoint(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    git_init(tmp_path)
    daemon = ResearchDaemon(RedThreadSettings(), tmp_path)
    daemon.phase3.start_session("tag")
    state = ResearchDaemonState(owner_id=daemon.owner_id, session_tag="tag", branch="autoresearch/tag", status="running")
    save_json_model(daemon.workspace.daemon_state_path, state)
    promotion_dir = daemon.workspace.promotions_dir / "promotion-test"
    promotion_dir.mkdir(parents=True, exist_ok=True)
    (promotion_dir / "promotion_checkpoint.json").write_text('{"checkpoint_id":"c","promotion_id":"p","proposal_id":"proposal-1","step":"manifest_written"}', encoding="utf-8")
    called: list[str] = []
    monkeypatch.setattr(daemon.promoter, "promote_latest", lambda: called.append("promote"))

    result = asyncio.run(daemon.run_once())

    assert called == ["promote"]
    assert result.last_completed_step == "promotion_completed"
