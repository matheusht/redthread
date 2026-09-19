"""Shared fixtures and mocks for Supervisor test suites."""

from __future__ import annotations

from redthread.config.settings import AlgorithmType, RedThreadSettings, TargetBackend
from redthread.models import (
    AttackOutcome,
    AttackResult,
    AttackTrace,
    CampaignConfig,
    ConversationTurn,
    JudgeVerdict,
    MitreAtlasTactic,
    Persona,
    PsychologicalTrigger,
)


def make_dry_run_settings(algorithm: str = "tap") -> RedThreadSettings:
    return make_settings(dry_run=True, algorithm=algorithm)


def make_live_settings(algorithm: str = "tap") -> RedThreadSettings:
    return make_settings(dry_run=False, algorithm=algorithm)


def make_settings(dry_run: bool, algorithm: str = "tap") -> RedThreadSettings:
    return RedThreadSettings(
        target_backend=TargetBackend.OLLAMA,
        target_model="llama3.2:3b",
        attacker_backend=TargetBackend.OLLAMA,
        attacker_model="llama3.2:3b",
        judge_backend=TargetBackend.OPENAI,
        judge_model="gpt-4o",
        openai_api_key="test-key",
        algorithm=AlgorithmType(algorithm),
        branching_factor=2,
        tree_depth=2,
        tree_width=3,
        dry_run=dry_run,
    )


def make_campaign_config(num_personas: int = 2) -> CampaignConfig:
    return CampaignConfig(
        objective="Test authorization bypass",
        target_system_prompt="You are a helpful assistant.",
        num_personas=num_personas,
        rubric_name="authorization_bypass",
    )


def make_persona(name: str = "Test Persona") -> Persona:
    return Persona(
        name=name,
        tactic=MitreAtlasTactic.INITIAL_ACCESS,
        technique="AML.T0051",
        cover_story="Routine audit",
        hidden_objective="Bypass authorization checks",
        system_prompt="You are a persistent auditor...",
        psychological_triggers=[PsychologicalTrigger.AUTHORITY],
    )


def make_mock_attack_result(
    persona: Persona,
    is_jailbreak: bool = False,
    score: float = 1.5,
) -> AttackResult:
    trace = AttackTrace(
        persona=persona,
        algorithm="tap",
        turns=[
            ConversationTurn(
                turn_number=1,
                attacker_prompt="Test attack prompt",
                target_response="Target response",
            )
        ],
        outcome=AttackOutcome.SUCCESS if is_jailbreak else AttackOutcome.FAILURE,
    )
    verdict = JudgeVerdict(
        score=score,
        raw_score=int(score),
        reasoning="Test reasoning",
        feedback="Test feedback",
        rubric_name="authorization_bypass",
        is_jailbreak=is_jailbreak,
    )
    return AttackResult(trace=trace, verdict=verdict, iterations_used=3, duration_seconds=0.5)
