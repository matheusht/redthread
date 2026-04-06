from __future__ import annotations

import subprocess
from pathlib import Path

from pytest import MonkeyPatch

from redthread.config.settings import AlgorithmType, RedThreadSettings
from redthread.research.git_ops import GitWorkspaceManager
from redthread.research.history import ObjectiveHistoryAnalyzer
from redthread.research.models import SupervisorCycleSummary
from redthread.research.phase3 import PhaseThreeHarness


def test_objective_history_analyzer_ranks_from_tsv(tmp_path: Path) -> None:
    results = tmp_path / "results.tsv"
    results.write_text(
        "\n".join(
            [
                "timestamp\trun_id\tmode\tlane\tobjective_slugs\tcampaign_ids\ttotal_campaigns\ttotal_results\tconfirmed_jailbreaks\tnear_misses\taverage_asr\taverage_score\tcomposite_score\tstatus\tdescription",
                "2026-01-01T00:00:00Z\tr1\texperiment\toffense\tauthorization_bypass|prompt_injection\tc1\t2\t6\t1\t2\t0.5\t3.0\t18.0\tkeep\trow1",
                "2026-01-02T00:00:00Z\tr2\tsupervised_lane\tregression\tsensitive_info_exfiltration\tc2\t1\t3\t0\t1\t0.0\t2.0\t4.0\tkeep\trow2",
            ]
        ),
        encoding="utf-8",
    )

    ranked = ObjectiveHistoryAnalyzer(results).rank()
    assert ranked
    assert ranked[0].slug in {"authorization_bypass", "prompt_injection"}


def test_phase_three_dynamic_lanes_prefers_ranked_slugs(tmp_path: Path) -> None:
    from redthread.config.settings import RedThreadSettings

    harness = PhaseThreeHarness(RedThreadSettings(), tmp_path)
    lanes = harness._dynamic_lanes(["system_prompt_exfiltration", "authorization_bypass"])
    assert lanes[0].lane == "offense"
    assert lanes[0].objective_slugs[0] == "system_prompt_exfiltration"
    assert lanes[2].lane == "control"


def test_git_workspace_manager_detects_dirty_tree(tmp_path: Path) -> None:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")
    (tmp_path / "README.md").write_text("hello\n", encoding="utf-8")
    _git(tmp_path, "add", "README.md")
    _git(tmp_path, "commit", "-m", "init")

    manager = GitWorkspaceManager(tmp_path)
    assert manager.current_branch()
    assert manager.head_commit()

    (tmp_path / "README.md").write_text("changed\n", encoding="utf-8")
    try:
        manager.ensure_clean()
    except RuntimeError as exc:
        assert "clean git tree" in str(exc)
    else:
        raise AssertionError("expected dirty tree detection")


async def test_phase_three_proposal_records_algorithm_override(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    harness = PhaseThreeHarness(RedThreadSettings(), tmp_path)
    harness.session_path.write_text(
        '{"tag":"tag","branch":"autoresearch/tag","base_commit":"abc1234"}',
        encoding="utf-8",
    )

    async def stub_run_cycle(
        self: object,
        baseline_first: bool,
        algorithm_override: AlgorithmType | None = None,
    ) -> SupervisorCycleSummary:
        assert baseline_first is False
        assert algorithm_override == AlgorithmType.MCTS
        return SupervisorCycleSummary(
            run_id="supervisor-1",
            accepted=True,
            winning_lane="offense",
            rationale="ok",
            lane_summaries=[],
        )

    monkeypatch.setattr("redthread.research.supervisor.PhaseTwoResearchHarness.run_cycle", stub_run_cycle)

    proposal = await harness.run_cycle(baseline_first=False, algorithm_override=AlgorithmType.MCTS)

    assert proposal.algorithm_override == "mcts"


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout.strip()
