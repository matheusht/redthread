from __future__ import annotations

import json
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from click.testing import CliRunner

from redthread.cli import main
from redthread.research.workspace import ResearchWorkspace
from tests.research_promotion_helpers import append_research_record, proposal_payload


def test_research_promote_cli_surfaces_weak_evidence(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    append_research_record(
        workspace,
        "trace-weak",
        validation_mode="dry_run",
        evidence_mode="sealed_dry_run_replay",
    )
    payload = proposal_payload(workspace, eligible_trace_ids=["trace-weak"])
    workspace.proposal_path("proposal-123").write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(main, ["research", "promote", "--dry-run"])

    assert result.exit_code == 0
    assert "Weak evidence: trace-weak" in result.output
    assert "Failure map:" in result.output
    assert "evidence_mode_not_promotable:sealed_dry_run_replay" in result.output


def test_research_promote_inspect_cli_surfaces_missing_and_failed_buckets(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    append_research_record(workspace, "trace-missing", with_report=False)
    payload = proposal_payload(workspace, eligible_trace_ids=["trace-missing"])
    workspace.proposal_path("proposal-123").write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    promote = CliRunner().invoke(main, ["research", "promote", "--dry-run"])
    assert promote.exit_code == 0

    inspect = CliRunner().invoke(main, ["research", "promote-inspect"])

    assert inspect.exit_code == 0
    assert "Missing:   trace-missing" in inspect.output
    assert "Weak:      trace-missing" in inspect.output
    assert "Fail map:" in inspect.output
    assert "missing_validation_report" in inspect.output
    assert "validation report missing" in inspect.output


def test_research_promote_inspect_cli_bridges_to_replay_case_failure_detail(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    append_research_record(workspace, "trace-benign-regression", benign_passed=False)
    payload = proposal_payload(workspace, eligible_trace_ids=["trace-benign-regression"])
    workspace.proposal_path("proposal-123").write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    promote = CliRunner().invoke(main, ["research", "promote", "--dry-run"])
    assert promote.exit_code == 0

    inspect = CliRunner().invoke(main, ["research", "promote-inspect"])

    assert inspect.exit_code == 0
    assert "Trace detail:" in inspect.output
    assert "trace-benign-regression: evidence=live_replay; passed=False;" in inspect.output
    assert "failed_cases=capital_france" in inspect.output
    assert "capital_france (benign) -> benign regression" in inspect.output
