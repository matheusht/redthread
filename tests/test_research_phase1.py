from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pytest import MonkeyPatch

from redthread.config.settings import AlgorithmType, RedThreadSettings
from redthread.research.baseline import run_objective
from redthread.research.ledger import ResearchLedger
from redthread.research.models import ResearchBatchSummary
from redthread.research.objectives import default_research_config, ensure_config
from redthread.research.scheduler import PhaseTwoScheduler
from redthread.research.supervisor import PhaseTwoResearchHarness
from redthread.research.workspace import ResearchWorkspace


def test_ensure_config_creates_default_file(tmp_path: Path) -> None:
    config_path = tmp_path / "autoresearch" / "config.json"
    config = ensure_config(config_path)

    assert config_path.exists()
    assert config.benchmark_objectives
    assert config.experiment_objectives


def test_research_ledger_writes_header_and_row(tmp_path: Path) -> None:
    ledger_path = tmp_path / "autoresearch" / "results.tsv"
    ledger = ResearchLedger(ledger_path)
    summary = ResearchBatchSummary(
        run_id="research-1234",
        mode="baseline",
        objective_slugs=["prompt_injection"],
        campaign_ids=["campaign-abc"],
        total_campaigns=1,
        total_results=3,
        confirmed_jailbreaks=1,
        near_misses=1,
        average_asr=0.5,
        average_score=3.2,
        composite_score=15.7,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )

    ledger.append(summary, status="keep", description="test row")
    rows = ledger_path.read_text(encoding="utf-8").strip().splitlines()

    assert len(rows) == 2
    assert rows[0].startswith("timestamp\trun_id\tmode")
    assert "research-1234" in rows[1]
    assert "test row" in rows[1]


def test_phase_two_scheduler_resolves_default_lanes() -> None:
    config = default_research_config()
    scheduler = PhaseTwoScheduler(config)

    lanes = scheduler.lanes()
    assert [lane.lane for lane in lanes] == ["offense", "regression", "control"]
    assert len(scheduler.objectives_for_lane(lanes[0])) == 2
    assert len(scheduler.objectives_for_lane(lanes[2])) == 4


def test_phase_two_decision_rejects_when_control_exceeds_thresholds(tmp_path: Path) -> None:
    phase_two = PhaseTwoResearchHarness(RedThreadSettings(), tmp_path)
    started = datetime.now(timezone.utc)
    lane_summaries = [
        ResearchBatchSummary(
            run_id="r1",
            mode="supervised_lane",
            lane="offense",
            objective_slugs=["authorization_bypass"],
            campaign_ids=["c1"],
            total_campaigns=1,
            total_results=3,
            confirmed_jailbreaks=1,
            near_misses=1,
            average_asr=0.5,
            average_score=3.5,
            composite_score=16.0,
            started_at=started,
            completed_at=started,
        ),
        ResearchBatchSummary(
            run_id="r2",
            mode="supervised_lane",
            lane="regression",
            objective_slugs=["prompt_injection"],
            campaign_ids=["c2"],
            total_campaigns=1,
            total_results=3,
            confirmed_jailbreaks=0,
            near_misses=1,
            average_asr=0.0,
            average_score=2.5,
            composite_score=4.5,
            started_at=started,
            completed_at=started,
        ),
        ResearchBatchSummary(
            run_id="r3",
            mode="supervised_lane",
            lane="control",
            objective_slugs=["prompt_injection"],
            campaign_ids=["c3"],
            total_campaigns=1,
            total_results=3,
            confirmed_jailbreaks=0,
            near_misses=0,
            average_asr=0.5,
            average_score=3.0,
            composite_score=5.5,
            started_at=started,
            completed_at=started,
        ),
    ]

    cycle = phase_two._decide(lane_summaries, started)
    assert cycle.accepted is False
    assert cycle.winning_lane == "offense"


def test_research_workspace_scopes_runtime_memory(tmp_path: Path) -> None:
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    settings = workspace.research_settings(RedThreadSettings())

    assert workspace.template_config_path.exists()
    assert workspace.runtime_config_path.exists()
    assert settings.memory_dir == workspace.research_memory_dir
    assert settings.research_runtime_dir == workspace.runtime_dir


def test_default_research_config_includes_mcts_and_crescendo() -> None:
    config = default_research_config()

    benchmark_algorithms = {objective.slug: objective.algorithm for objective in config.benchmark_objectives}
    experiment_algorithms = {objective.slug: objective.algorithm for objective in config.experiment_objectives}

    assert benchmark_algorithms["authorization_bypass"] == "crescendo"
    assert benchmark_algorithms["sensitive_info_exfiltration"] == "mcts"
    assert experiment_algorithms["system_prompt_exfiltration"] == "crescendo"
    assert experiment_algorithms["sensitive_info_exfiltration"] == "mcts"


async def test_run_objective_algorithm_override_forces_selected_algorithm(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class StubEngine:
        def __init__(self, settings: RedThreadSettings) -> None:
            captured["settings"] = settings

        async def run(self, config: object) -> object:
            class Verdict:
                score = 4.6
                is_jailbreak = True

            class ResultItem:
                verdict = Verdict()

            class Campaign:
                id = "campaign-1"
                attack_success_rate = 1.0
                average_score = 4.6
                results = [ResultItem()]

            captured["config"] = config
            return Campaign()

    monkeypatch.setattr("redthread.research.baseline.RedThreadEngine", StubEngine)
    objective = default_research_config().experiment_objectives[0].model_copy(update={"algorithm": "tap"})

    await run_objective(
        RedThreadSettings(),
        objective,
        algorithm_override=AlgorithmType.CRESCENDO,
    )

    settings = captured["settings"]
    assert isinstance(settings, RedThreadSettings)
    assert settings.algorithm == AlgorithmType.CRESCENDO


async def test_run_objective_applies_mcts_fields(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, RedThreadSettings] = {}

    class StubEngine:
        def __init__(self, settings: RedThreadSettings) -> None:
            captured["settings"] = settings

        async def run(self, config: object) -> object:
            class Campaign:
                id = "campaign-1"
                attack_success_rate = 0.0
                average_score = 1.0
                results: list[object] = []

            return Campaign()

    monkeypatch.setattr("redthread.research.baseline.RedThreadEngine", StubEngine)
    objective = default_research_config().benchmark_objectives[2]

    await run_objective(RedThreadSettings(), objective)

    settings = captured["settings"]
    assert settings.algorithm == AlgorithmType.MCTS
    assert settings.mcts_simulations == objective.simulations
    assert settings.mcts_max_depth == objective.max_depth
    assert settings.mcts_strategy_count == objective.strategy_count
    assert settings.mcts_max_budget_tokens == objective.budget_tokens
