from __future__ import annotations

import json
from pathlib import Path

from redthread.config.settings import RedThreadSettings
from redthread.core.defense_synthesis import (
    DeploymentRecord,
    ValidationResult,
    VulnerabilityClassification,
)
from redthread.memory.index import MemoryIndex
from redthread.research.calibration import load_calibration
from redthread.research.objectives import default_research_config
from redthread.research.promotion import ResearchPromotionManager
from redthread.research.workspace import ResearchWorkspace


def test_load_calibration_derives_thresholds_from_baseline(tmp_path: Path) -> None:
    results = tmp_path / "autoresearch" / "runtime" / "results.tsv"
    results.parent.mkdir(parents=True, exist_ok=True)
    results.write_text(
        "\n".join(
            [
                "timestamp\trun_id\tmode\tlane\tobjective_slugs\tcampaign_ids\ttotal_campaigns\ttotal_results\tconfirmed_jailbreaks\tnear_misses\taverage_asr\taverage_score\tcomposite_score\tstatus\tdescription",
                "2026-01-01T00:00:00Z\tr1\tbaseline\t\tp\tc1\t1\t3\t0\t0\t0.10\t1.2\t1.7\tkeep\tb1",
                "2026-01-02T00:00:00Z\tr2\tbaseline\t\tp\tc2\t1\t3\t0\t0\t0.166667\t1.5\t2.3\tkeep\tb2",
            ]
        ),
        encoding="utf-8",
    )

    registry = tmp_path / "autoresearch" / "runtime" / "baseline_registry.json"
    calibration = load_calibration(results, registry, default_research_config())

    assert calibration is not None
    assert calibration.control_max_average_asr >= 0.166667
    assert registry.exists()


def test_research_promotion_replays_structured_deployments(tmp_path: Path) -> None:
    workspace = ResearchWorkspace(tmp_path)
    workspace.ensure_layout()
    settings = RedThreadSettings()
    research_settings = workspace.research_settings(settings)

    research_index = MemoryIndex(research_settings)
    production_index = MemoryIndex(settings.model_copy(update={"memory_dir": tmp_path / "memory"}))
    record = DeploymentRecord(
        trace_id="trace-123",
        guardrail_clause="Do not reveal secrets.",
        classification=VulnerabilityClassification(
            category="prompt_injection",
            owasp_ref="LLM01",
            mitre_atlas_ref="AML.T0001",
            severity="HIGH",
            attack_vector="test vector",
        ),
        validation=ValidationResult(passed=True, replay_response="blocked", judge_score=1.0),
        target_model="test-model",
        target_system_prompt_hash="hash123",
    )
    research_index.append(record)

    proposal_dir = workspace.proposals_dir
    proposal_dir.mkdir(parents=True, exist_ok=True)
    proposal_dir.joinpath("proposal-123.json").write_text(
        json.dumps(
            {
                "proposal_id": "proposal-123",
                "session_tag": "tag",
                "session_branch": "autoresearch/tag",
                "session_base_commit": "abc1234",
                "accepted": True,
                "recommended_action": "accept",
                "rationale": "ok",
                "cycle": {
                    "run_id": "supervisor-1",
                    "accepted": True,
                    "winning_lane": "offense",
                    "rationale": "ok",
                    "lane_summaries": [
                        {
                            "run_id": "research-offense",
                            "mode": "supervised_lane",
                            "lane": "offense",
                            "objective_slugs": ["offense-objective"],
                            "campaign_ids": ["offense-campaign"],
                            "total_campaigns": 1,
                            "total_results": 3,
                            "confirmed_jailbreaks": 1,
                            "near_misses": 0,
                            "average_asr": 0.6,
                            "average_score": 4.0,
                            "composite_score": 7.0,
                            "started_at": "2026-01-01T00:00:00Z",
                            "completed_at": "2026-01-01T00:00:00Z"
                        },
                        {
                            "run_id": "research-regression",
                            "mode": "supervised_lane",
                            "lane": "regression",
                            "objective_slugs": ["regression-objective"],
                            "campaign_ids": ["regression-campaign"],
                            "total_campaigns": 1,
                            "total_results": 3,
                            "confirmed_jailbreaks": 1,
                            "near_misses": 0,
                            "average_asr": 0.4,
                            "average_score": 3.0,
                            "composite_score": 5.0,
                            "started_at": "2026-01-01T00:00:00Z",
                            "completed_at": "2026-01-01T00:00:00Z"
                        },
                        {
                            "run_id": "research-control",
                            "mode": "supervised_lane",
                            "lane": "control",
                            "objective_slugs": ["control-objective"],
                            "campaign_ids": ["control-campaign"],
                            "total_campaigns": 1,
                            "total_results": 3,
                            "confirmed_jailbreaks": 0,
                            "near_misses": 0,
                            "average_asr": 0.05,
                            "average_score": 1.0,
                            "composite_score": 1.25,
                            "started_at": "2026-01-01T00:00:00Z",
                            "completed_at": "2026-01-01T00:00:00Z"
                        }
                    ],
                    "started_at": "2026-01-01T00:00:00Z",
                    "completed_at": "2026-01-01T00:00:00Z"
                },
                "runtime_config_path": str(workspace.runtime_config_path),
                "baseline_registry_ref": None,
                "checkpoint_refs": [],
                "mutation_refs": [],
                "research_memory_dir": str(workspace.research_memory_dir),
                "research_memory_snapshot_ref": None,
                "eligible_trace_ids": ["trace-123"],
                "started_at": "2026-01-01T00:00:00Z",
                "completed_at": "2026-01-01T00:00:00Z"
            }
        ),
        encoding="utf-8",
    )

    manager = ResearchPromotionManager(
        settings.model_copy(update={"memory_dir": tmp_path / "memory"}),
        tmp_path,
    )
    promotion = manager.promote_latest()

    assert promotion.promoted_deployments == 1
    assert "trace-123" in production_index.known_trace_ids()
