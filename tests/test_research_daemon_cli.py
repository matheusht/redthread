from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner
from pytest import MonkeyPatch

from redthread.cli import main


def test_research_daemon_status_cli(monkeypatch: MonkeyPatch) -> None:
    class StubDaemon:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def status(self) -> SimpleNamespace:
            return SimpleNamespace(
                session_tag="tag",
                branch="autoresearch/tag",
                active_lock=True,
                stale_lock=False,
                last_heartbeat_at="now",
                current_step="proposal_emitted",
                status="awaiting_review",
                consecutive_failures=0,
                cooldown_until=None,
                latest_proposal_id="proposal-123",
                latest_candidate_id="candidate-123",
            )

    monkeypatch.setattr("redthread.research.daemon.ResearchDaemon", StubDaemon)
    result = CliRunner().invoke(main, ["research", "daemon", "status"])
    assert result.exit_code == 0
    assert "autoresearch/tag" in result.output
    assert "awaiting_review" in result.output
    assert "manual Phase 3 review" in result.output


def test_research_daemon_start_cli(monkeypatch: MonkeyPatch) -> None:
    class StubDaemon:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        async def start(self, create_session_tag: str | None = None) -> SimpleNamespace:
            assert create_session_tag == "tag"
            return SimpleNamespace(
                session_tag="tag",
                branch="autoresearch/tag",
                status="awaiting_review",
                last_completed_step="proposal_emitted",
                consecutive_failures=0,
                latest_proposal_id="proposal-123",
                latest_candidate_id="candidate-123",
            )

    monkeypatch.setattr("redthread.research.daemon.ResearchDaemon", StubDaemon)
    result = CliRunner().invoke(main, ["research", "daemon", "start", "--create-session", "tag"])
    assert result.exit_code == 0
    assert "Research daemon stopped" in result.output
    assert "awaiting_review" in result.output
    assert "manual Phase 3 review" in result.output


def test_research_resume_cli(monkeypatch: MonkeyPatch) -> None:
    class StubDaemon:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        async def resume(self, create_session_tag: str | None = None) -> SimpleNamespace:
            assert create_session_tag == "tag"
            return SimpleNamespace(
                session_tag="tag",
                status="awaiting_review",
                last_completed_step="proposal_emitted",
                latest_proposal_id="proposal-123",
            )

    monkeypatch.setattr("redthread.research.daemon.ResearchDaemon", StubDaemon)
    result = CliRunner().invoke(main, ["research", "resume", "--create-session", "tag"])
    assert result.exit_code == 0
    assert "awaiting_review" in result.output
    assert "proposal-123" in result.output
    assert "manual Phase 3 review" in result.output


def test_research_daemon_stop_cli(monkeypatch: MonkeyPatch) -> None:
    class StubDaemon:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def stop(self) -> SimpleNamespace:
            return SimpleNamespace(session_tag="tag", status="stop_requested")

    monkeypatch.setattr("redthread.research.daemon.ResearchDaemon", StubDaemon)
    result = CliRunner().invoke(main, ["research", "daemon", "stop"])
    assert result.exit_code == 0
    assert "stop requested" in result.output


def test_research_checkpoints_cli(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    checkpoint = tmp_path / "autoresearch" / "runtime" / "checkpoints" / "phase2-offense.json"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.write_text('{"checkpoint_id":"phase2-offense"}', encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(main, ["research", "checkpoints", "list"])
    assert result.exit_code == 0
    assert "phase2-offense.json" in result.output

    result = CliRunner().invoke(main, ["research", "checkpoints", "inspect", "--path", str(checkpoint)])
    assert result.exit_code == 0
    assert "checkpoint_id" in result.output
