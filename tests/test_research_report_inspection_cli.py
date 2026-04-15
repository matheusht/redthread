from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner
from pytest import MonkeyPatch

from redthread.cli import main
from redthread.config.settings import RedThreadSettings
from redthread.memory.index import MemoryIndex
from redthread.research.workspace import ResearchWorkspace
from tests.research_promotion_helpers import append_research_record


def test_research_report_inspect_lists_reports_from_research_memory(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    append_research_record(workspace, "trace-1")
    append_research_record(workspace, "trace-2")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(main, ["research", "report-inspect"])

    assert result.exit_code == 0
    assert "trace-1" in result.output
    assert "trace-2" in result.output
    assert "Source:      research" in result.output


def test_research_report_inspect_filters_production_memory_by_trace_id(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    append_research_record(workspace, "trace-prod")
    research_record = MemoryIndex(workspace.research_settings(RedThreadSettings())).iter_deployments()[0]
    settings = RedThreadSettings().model_copy(update={"memory_dir": tmp_path / "memory"})
    MemoryIndex(settings).append(research_record)

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        main,
        ["research", "report-inspect", "--memory-source", "production", "--trace-id", "trace-prod"],
    )

    assert result.exit_code == 0
    assert "trace-prod" in result.output
    assert "Source:      production" in result.output
    assert "default-defense-replay-v4" in result.output
    assert "Replay cnt:" in result.output
    assert "Exploit cnt:" in result.output
    assert "Utility cnt:" in result.output


def test_research_report_inspect_fails_when_trace_has_no_validation_report(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    append_research_record(workspace, "trace-missing-report", with_report=False)

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        main,
        ["research", "report-inspect", "--trace-id", "trace-missing-report"],
    )

    assert result.exit_code != 0
    assert "has no validation report" in result.output
