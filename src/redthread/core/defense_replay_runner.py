"""Structured replay runner for defense validation."""

from __future__ import annotations

from typing import Protocol

from redthread.core.defense_evidence import LIVE_REPLAY, SEALED_DRY_RUN_REPLAY
from redthread.core.defense_models import ReplayCaseResult, ValidationResult
from redthread.core.defense_replay_cases import run_benign_cases, run_exploit_cases, to_benign_check
from redthread.core.defense_replay_fixtures import build_default_replay_suite, render_replay_prompt
from redthread.models import ConversationTurn


class ReplayTarget(Protocol):
    async def send(self, prompt: str, conversation_id: str = "") -> str: ...


class ReplayJudge(Protocol):
    def evaluate_turn(self, turn: ConversationTurn, rubric_name: str = "authorization_bypass") -> float: ...


class DefenseReplayRunner:
    """Execute exploit + benign replay cases for a proposed guardrail."""

    def __init__(self, success_threshold: float, authorization_policies: list | None = None) -> None:
        self.success_threshold = success_threshold
        self.authorization_policies = authorization_policies

    async def run_dry(self, attack_payload: str, guardrail_clause: str) -> ValidationResult:
        suite = build_default_replay_suite(attack_payload)
        exploit_cases = [
            ReplayCaseResult(
                case_id=case.case_id,
                kind="exploit",
                prompt=render_replay_prompt(guardrail_clause, case.attack_payload),
                response="[dry-run] Guardrail blocked replay.",
                passed=True,
                rubric_name=case.rubric_name,
                judge_score=1.0,
            )
            for case in suite.exploit_cases
        ]
        benign_cases = [
            ReplayCaseResult(
                case_id=case.case_id,
                kind="benign",
                prompt=render_replay_prompt(guardrail_clause, case.prompt),
                response="[dry-run] benign prompt preserved.",
                passed=True,
                matched_keywords=list(case.required_terms or case.any_of_terms),
            )
            for case in suite.benign_cases
        ]
        return ValidationResult(
            passed=True,
            replay_response=exploit_cases[0].response,
            judge_score=1.0,
            exploit_replay_passed=True,
            benign_passed=True,
            benign_checks=[to_benign_check(case) for case in benign_cases],
            replay_cases=[*exploit_cases, *benign_cases],
            replay_suite_id=suite.suite_id,
            validation_mode="dry_run",
            evidence_mode=SEALED_DRY_RUN_REPLAY,
        )

    async def run_live(
        self,
        *,
        target: ReplayTarget,
        judge: ReplayJudge,
        attack_payload: str,
        guardrail_clause: str,
        trace_id: str,
        rubric_name: str = "authorization_bypass",
    ) -> ValidationResult:
        suite = build_default_replay_suite(attack_payload)
        exploit_cases, replay_response, exploit_scores = await run_exploit_cases(
            suite.exploit_cases,
            target=target,
            judge=judge,
            guardrail_clause=guardrail_clause,
            trace_id=trace_id,
            rubric_name=rubric_name,
            success_threshold=self.success_threshold,
            authorization_policies=self.authorization_policies,
        )
        benign_cases, benign_checks = await run_benign_cases(
            suite.benign_cases,
            target=target,
            guardrail_clause=guardrail_clause,
            trace_id=trace_id,
            authorization_policies=self.authorization_policies,
        )
        exploit_passed = bool(exploit_cases) and all(case.passed for case in exploit_cases)
        benign_passed = bool(benign_checks) and all(check.passed for check in benign_checks)
        failures = [case.failure_reason for case in [*exploit_cases, *benign_cases] if case.failure_reason]
        return ValidationResult(
            passed=exploit_passed and benign_passed,
            replay_response=replay_response,
            judge_score=max(exploit_scores, default=0.0),
            exploit_replay_passed=exploit_passed,
            benign_passed=benign_passed,
            benign_checks=benign_checks,
            replay_cases=[*exploit_cases, *benign_cases],
            replay_suite_id=suite.suite_id,
            validation_mode="live",
            evidence_mode=LIVE_REPLAY,
            failure_reason="; ".join(failures),
        )
