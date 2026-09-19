"""Unit tests for automatic workspace rollback on failure in ResearchDaemon (Issue #101)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from redthread.config.settings import RedThreadSettings
from redthread.research.daemon import ResearchDaemon
from redthread.research.daemon_models import ResearchDaemonState
from redthread.research.daemon_runtime import ensure_session, save_daemon_state
from tests.research_promotion_helpers import git_init


@pytest.mark.asyncio
async def test_daemon_rolls_back_workspace_on_cycle_failure(tmp_path: Path) -> None:
    git_init(tmp_path)
    settings = RedThreadSettings()
    daemon = ResearchDaemon(settings, tmp_path)
    ensure_session(daemon.phase3, "test-session")
    save_daemon_state(
        daemon.workspace,
        ResearchDaemonState(owner_id="test", session_tag="test-session", branch="main"),
    )

    daemon.git.has_non_artifact_changes = MagicMock(return_value=True)
    daemon.mutator.revert_latest = MagicMock()

    # Simulate failure handling
    daemon._handle_failure("test failure occurred during cycle")

    assert daemon.mutator.revert_latest.called
