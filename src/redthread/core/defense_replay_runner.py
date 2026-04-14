"""Structured replay runner for defense validation.

Builds a replay suite from the isolated exploit segment plus the sealed benign
pack, executes the cases against a guardrail-patched target, and returns a
ValidationResult with per-case evidence.
"""

from __future__ import annotations

from typing import Protocol

from redthread.core.defense_assets import evaluate_benign_response
from redthread.core.defense_models import BenignValidationCheck, ReplayCaseResult, ValidationResult
from redthread.core.defense_replay_fixtures import build_default_replay_suite, render_replay_prompt
from redthread.models import ConversationTurn


class ReplayTarget(Protocol):
    """Structural target interface required by live defense replay."""

    async def send(self, prompt: str, conversation_id: str = "") -> str: ...


class ReplayJudge(Protocol):
    """Structural judge interface required by live defense replay."""

    def evaluate_turn(self, turn: ConversationTurn, rubric_name: str = "authorization_bypass") -> float: ...


class DefenseReplayRunner:
    """Execute exploit + benign replay cases for a proposed guardrail."""

    def __init__(self, success_threshold: float) -> None:
        self.success_threshold = success_threshold

    async def run_dry(self, attack_payload: str, guardrail_clause: str) -> ValidationResult:
        """Return a deterministic sealed replay result for dry-run mode."""
        suite = build_default_replay_suite(attack_payload)
        exploit_case = ReplayCaseResult(
            case_id=suite.exploit.case_id,
            kind="exploit",
            prompt=render_replay_prompt(guardrail_clause, suite.exploit.attack_payload),
            response="[dry-run] Guardrail blocked replay.",
            passed=True,
            rubric_name=suite.exploit.rubric_name,
            judge_score=1.0,
        )
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
            replay_response=exploit_case.response,
            judge_score=1.0,
            exploit_replay_passed=True,
            benign_passed=True,
            benign_checks=[self._to_benign_check(case) for case in benign_cases],
            replay_cases=[exploit_case, *benign_cases],
            replay_suite_id=suite.suite_id,
            validation_mode="dry_run",
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
        """Run replay cases against a live patched target and score the results."""
        suite = build_default_replay_suite(attack_payload)
        exploit_prompt = render_replay_prompt(guardrail_clause, suite.exploit.attack_payload)
        replay_response = await target.send(
            prompt=exploit_prompt,
            conversation_id=f"sandbox-replay-{trace_id}",
        )
        replay_turn = ConversationTurn(
            turn_number=1,
            attacker_prompt=attack_payload,
            target_response=replay_response,
        )
        residual_score = judge.evaluate_turn(replay_turn, rubric_name=suite.exploit.rubric_name or rubric_name)
        exploit_passed = residual_score < self.success_threshold
        exploit_case = ReplayCaseResult(
            case_id=suite.exploit.case_id,
            kind="exploit",
            prompt=exploit_prompt,
            response=replay_response,
            passed=exploit_passed,
            rubric_name=suite.exploit.rubric_name or rubric_name,
            judge_score=residual_score,
            failure_reason=(
                ""
                if exploit_passed
                else f"exploit replay score {residual_score:.2f} >= threshold {self.success_threshold:.2f}"
            ),
        )

        benign_cases: list[ReplayCaseResult] = []
        benign_checks = []
        for case in suite.benign_cases:
            benign_prompt = render_replay_prompt(guardrail_clause, case.prompt)
            response = await target.send(
                prompt=benign_prompt,
                conversation_id=f"sandbox-benign-{trace_id}-{case.case_id}",
            )
            check = evaluate_benign_response(case, response)
            benign_checks.append(check)
            benign_cases.append(
                ReplayCaseResult(
                    case_id=case.case_id,
                    kind="benign",
                    prompt=benign_prompt,
                    response=response,
                    passed=check.passed,
                    matched_keywords=list(check.matched_keywords),
                    missing_keywords=list(check.missing_keywords),
                    refusal_detected=check.refusal_detected,
                    failure_reason=check.failure_reason,
                )
            )

        benign_passed = bool(benign_checks) and all(check.passed for check in benign_checks)
        failures = [case.failure_reason for case in [exploit_case, *benign_cases] if case.failure_reason]
        return ValidationResult(
            passed=exploit_passed and benign_passed,
            replay_response=replay_response,
            judge_score=residual_score,
            exploit_replay_passed=exploit_passed,
            benign_passed=benign_passed,
            benign_checks=benign_checks,
            replay_cases=[exploit_case, *benign_cases],
            replay_suite_id=suite.suite_id,
            validation_mode="live",
            failure_reason="; ".join(failures),
        )

    def _to_benign_check(self, case: ReplayCaseResult) -> BenignValidationCheck:
        return BenignValidationCheck(
            case_id=case.case_id,
            prompt=case.prompt,
            response=case.response,
            passed=case.passed,
            matched_keywords=list(case.matched_keywords),
            missing_keywords=list(case.missing_keywords),
            refusal_detected=case.refusal_detected,
            failure_reason=case.failure_reason,
        )
