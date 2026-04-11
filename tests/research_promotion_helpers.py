from __future__ import annotations

import json
import subprocess
from pathlib import Path

from redthread.config.settings import RedThreadSettings
from redthread.core.defense_models import ReplayCaseResult
from redthread.core.defense_reporting_models import DefenseValidationReport
from redthread.core.defense_synthesis import (
    DeploymentRecord,
    ValidationResult,
    VulnerabilityClassification,
)
from redthread.memory.index import MemoryIndex
from redthread.research.workspace import ResearchWorkspace


def append_research_record(
    workspace: ResearchWorkspace,
    trace_id: str,
    *,
    with_report: bool = True,
    validation_mode: str = "live",
    exploit_replay_passed: bool = True,
    benign_passed: bool = True,
    include_replay_cases: bool = True,
) -> None:
    settings = RedThreadSettings()
    index = MemoryIndex(workspace.research_settings(settings))
    index.append(
        DeploymentRecord(
            trace_id=trace_id,
            guardrail_clause="Do not reveal secrets.",
            classification=VulnerabilityClassification(
                category="prompt_injection",
                owasp_ref="LLM01",
                mitre_atlas_ref="AML.T0001",
                severity="HIGH",
                attack_vector="test vector",
            ),
            validation=ValidationResult(
                passed=exploit_replay_passed and benign_passed,
                replay_response="blocked",
                judge_score=(1.0 if exploit_replay_passed else 4.9),
                exploit_replay_passed=exploit_replay_passed,
                benign_passed=benign_passed,
                replay_cases=(
                    [
                        ReplayCaseResult(
                            case_id="exploit_replay",
                            kind="exploit",
                            prompt="[SYSTEM]: test\n\n[USER]: attack",
                            response="blocked",
                            passed=exploit_replay_passed,
                            judge_score=(1.0 if exploit_replay_passed else 4.9),
                        ),
                        ReplayCaseResult(
                            case_id="capital_france",
                            kind="benign",
                            prompt="[SYSTEM]: test\n\n[USER]: benign",
                            response="Paris",
                            passed=benign_passed,
                            failure_reason=("" if benign_passed else "benign regression"),
                        ),
                    ]
                    if include_replay_cases
                    else []
                ),
                replay_suite_id="default-defense-replay-v1",
                validation_mode=validation_mode,
            ),
            target_model="test-model",
            target_system_prompt_hash="hash123",
            validation_report=(
                DefenseValidationReport(
                    trace_id=trace_id,
                    replay_suite_id="default-defense-replay-v1",
                    validation_mode=validation_mode,
                    exploit_case_ids=["exploit_replay"],
                    benign_case_ids=["capital_france"],
                    failed_case_ids=[],
                    blocked_attack_summary="exploit replay blocked",
                    benign_utility_summary="benign suite 1/1 passed",
                    guardrail_clause="Do not reveal secrets.",
                    rationale="test rationale",
                )
                if with_report
                else None
            ),
        )
    )


def proposal_payload(
    workspace: ResearchWorkspace,
    *,
    eligible_trace_ids: list[str],
    control_asr: float = 0.05,
    snapshot_ref: str | None = None,
) -> dict[str, object]:
    workspace.runtime_config_path.write_text(
        json.dumps({"control_max_average_asr": 0.1, "control_max_average_score": 2.5}),
        encoding="utf-8",
    )
    return {
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
                lane("offense", 0.6, 4.2),
                lane("regression", 0.4, 3.0),
                lane("control", control_asr, 1.0),
            ],
            "started_at": "2026-01-01T00:00:00Z",
            "completed_at": "2026-01-01T00:00:00Z",
        },
        "runtime_config_path": str(workspace.runtime_config_path),
        "baseline_registry_ref": None,
        "checkpoint_refs": [],
        "mutation_refs": [],
        "research_memory_dir": str(workspace.research_memory_dir),
        "research_memory_snapshot_ref": snapshot_ref,
        "eligible_trace_ids": eligible_trace_ids,
        "research_plane_status": "accepted",
        "promotion_eligibility_status": "eligible_for_promotion",
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:00:00Z",
    }


def lane(name: str, asr: float, score: float) -> dict[str, object]:
    return {
        "run_id": f"research-{name}",
        "mode": "supervised_lane",
        "lane": name,
        "objective_slugs": [f"{name}-objective"],
        "campaign_ids": [f"{name}-campaign"],
        "total_campaigns": 1,
        "total_results": 3,
        "confirmed_jailbreaks": 1 if name != "control" else 0,
        "near_misses": 0,
        "average_asr": asr,
        "average_score": score,
        "composite_score": score + (asr * 5),
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:00:00Z",
    }


def git_init(root: Path) -> None:
    git(root, "init")
    git(root, "config", "user.email", "test@example.com")
    git(root, "config", "user.name", "Test User")
    (root / "README.md").write_text("hello\n", encoding="utf-8")
    git(root, "add", "README.md")
    git(root, "commit", "-m", "init")


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout.strip()
