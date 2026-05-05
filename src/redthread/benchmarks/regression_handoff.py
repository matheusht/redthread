"""Prompt-safe regression handoff artifacts for benchmark replay."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from redthread.benchmarks.campaigns import BenchmarkCampaignDraft
from redthread.benchmarks.jailbreak_fixtures import JailbreakBenchmarkFixture
from redthread.benchmarks.material_vault import BenchmarkMaterialManifest
from redthread.core.regression_cases import RegressionCaseError, regression_case_from_attack_result
from redthread.models import AttackResult

_REDACTED_PROMPT = "[redacted: reviewed benchmark prompt material remains in private vault]"
_REDACTED_RESPONSE = "[redacted: target response may echo reviewed benchmark material]"
_REDACTED_TARGET_PROMPT = "[redacted: target system prompt stays outside public benchmark artifacts]"


class BenchmarkRegressionHandoffError(ValueError):
    """Raised when a regression handoff artifact cannot be written."""


class BenchmarkRegressionSkip(BaseModel):
    """Reason one replay result did not become a regression case."""

    result_id: str
    trace_id: str
    fixture_id: str
    reason: str


class BenchmarkRegressionCaseSummary(BaseModel):
    """Prompt-safe regression case handoff row."""

    regression_case_id: str
    source_finding_id: str
    fixture_id: str
    risk_plugin_id: str
    strategy_id: str
    judge_score: float
    severity_at_creation: str
    expected_safe_behavior: str
    material_ref: str
    material_sha256: str
    regression_case: dict[str, Any]


class BenchmarkRegressionHandoffArtifact(BaseModel):
    """Prompt-safe artifact for moving confirmed benchmark findings to regression work."""

    schema_version: Literal["redthread.jailbreak_benchmark_regression_handoff.v1"] = (
        "redthread.jailbreak_benchmark_regression_handoff.v1"
    )
    kind: str = "benchmark_regression_handoff"
    fixture_id: str
    manifest_ref: str
    material_ref: str
    material_sha256: str
    reviewed_by: str
    reviewed_at: str
    reviewers: list[str] = Field(default_factory=list)
    allowed_target_ids: list[str] = Field(default_factory=list)
    created_cases: list[BenchmarkRegressionCaseSummary] = Field(default_factory=list)
    skipped_results: list[BenchmarkRegressionSkip] = Field(default_factory=list)
    raw_prompt_policy: str = "raw prompt bodies are redacted; replay uses private vault material refs"

    def summary_lines(self) -> list[str]:
        """Return operator-readable summary lines."""
        return [
            "Regression handoff: prompt-safe artifact",
            f"Fixture: {self.fixture_id}",
            f"Regression cases created: {len(self.created_cases)}",
            f"Results skipped: {len(self.skipped_results)}",
            "Raw prompt bodies: redacted from artifact",
        ]


def build_benchmark_regression_handoff(
    draft: BenchmarkCampaignDraft,
    results: list[AttackResult],
    *,
    manifest: BenchmarkMaterialManifest,
    manifest_ref: str,
) -> BenchmarkRegressionHandoffArtifact:
    """Build a prompt-safe handoff from approved replay results."""
    fixture = _single_fixture(draft)
    created_cases: list[BenchmarkRegressionCaseSummary] = []
    skipped_results: list[BenchmarkRegressionSkip] = []
    for result in results:
        if not result.verdict.is_jailbreak:
            skipped_results.append(_skip(result, fixture.id, "verdict_not_jailbreak"))
            continue
        try:
            regression_case = regression_case_from_attack_result(
                result,
                expected_safe_behavior=fixture.expected_safe_behavior,
                replay_schedule="manual",
            )
        except RegressionCaseError:
            skipped_results.append(_skip(result, fixture.id, "not_replayable"))
            continue
        safe_case = regression_case.model_copy(
            update={"minimized_trace": _redacted_trace(regression_case.minimized_trace)}
        )
        created_cases.append(
            BenchmarkRegressionCaseSummary(
                regression_case_id=safe_case.id,
                source_finding_id=safe_case.source_finding_id,
                fixture_id=fixture.id,
                risk_plugin_id=safe_case.risk_plugin_id,
                strategy_id=safe_case.strategy_id,
                judge_score=result.verdict.score,
                severity_at_creation=safe_case.severity_at_creation,
                expected_safe_behavior=safe_case.expected_safe_behavior,
                material_ref=manifest.material_ref,
                material_sha256=manifest.sha256,
                regression_case=safe_case.model_dump(mode="json"),
            )
        )
    return BenchmarkRegressionHandoffArtifact(
        fixture_id=fixture.id,
        manifest_ref=manifest_ref,
        material_ref=manifest.material_ref,
        material_sha256=manifest.sha256,
        reviewed_by=manifest.reviewed_by,
        reviewed_at=manifest.reviewed_at,
        reviewers=manifest.reviewers,
        allowed_target_ids=manifest.allowed_target_ids,
        created_cases=created_cases,
        skipped_results=skipped_results,
    )


def write_benchmark_regression_handoff_artifact(
    artifact: BenchmarkRegressionHandoffArtifact,
    output_path: str | Path,
) -> str:
    """Write a prompt-safe benchmark regression handoff JSON artifact."""
    path = Path(output_path).expanduser()
    if path.exists() and path.is_dir():
        msg = f"benchmark regression handoff output path is a directory: {output_path}"
        raise BenchmarkRegressionHandoffError(msg)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(artifact.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        msg = f"could not write benchmark regression handoff artifact: {output_path}"
        raise BenchmarkRegressionHandoffError(msg) from exc
    return str(path)


def _single_fixture(draft: BenchmarkCampaignDraft) -> JailbreakBenchmarkFixture:
    if len(draft.fixtures) != 1:
        msg = "benchmark regression handoff requires exactly one fixture"
        raise BenchmarkRegressionHandoffError(msg)
    return draft.fixtures[0]


def _skip(result: AttackResult, fixture_id: str, reason: str) -> BenchmarkRegressionSkip:
    return BenchmarkRegressionSkip(
        result_id=result.id,
        trace_id=result.trace.id,
        fixture_id=fixture_id,
        reason=reason,
    )


def _redacted_trace(trace: dict[str, Any]) -> dict[str, Any]:
    safe_trace = dict(trace)
    turns = safe_trace.get("turns", [])
    if isinstance(turns, list):
        safe_trace["turns"] = [_redacted_turn(turn) for turn in turns]
    if "target_system_prompt" in safe_trace:
        safe_trace["target_system_prompt"] = _REDACTED_TARGET_PROMPT
    safe_trace["raw_prompt_policy"] = "reviewed prompt material stays in the private benchmark vault"
    return safe_trace


def _redacted_turn(turn: object) -> object:
    if not isinstance(turn, dict):
        return turn
    safe_turn = dict(turn)
    if "attacker_prompt" in safe_turn:
        safe_turn["attacker_prompt"] = _REDACTED_PROMPT
    if "target_response_excerpt" in safe_turn:
        safe_turn["target_response_excerpt"] = _REDACTED_RESPONSE
    if "target_response" in safe_turn:
        safe_turn["target_response"] = _REDACTED_RESPONSE
    return safe_turn
