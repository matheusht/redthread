"""Live baseline replay attachment for launch-readiness campaigns."""

from __future__ import annotations

import hashlib

from redthread.config.settings import RedThreadSettings
from redthread.core.defense_replay_runner import DefenseReplayRunner
from redthread.evaluation.judge import JudgeAgent
from redthread.models import CampaignConfig, CampaignResult
from redthread.pyrit_adapters import targets as target_builders


async def attach_live_baseline_replay(
    campaign: CampaignResult,
    *,
    settings: RedThreadSettings,
    campaign_config: CampaignConfig,
) -> None:
    """Run one bounded final-turn probe per clean trace; retain safe evidence only."""
    if not campaign.results:
        return
    runner = DefenseReplayRunner(settings.success_threshold)
    target = target_builders.build_target(settings)
    validations = []
    try:
        judge = JudgeAgent(settings)
        for result in campaign.results:
            if result.verdict.is_jailbreak:
                continue
            attack_payload = next(
                (turn.attacker_prompt for turn in reversed(result.trace.turns) if turn.attacker_prompt),
                "launch readiness baseline probe",
            )
            validations.append(
                await runner.run_live_baseline(
                    target=target,
                    judge=judge,
                    attack_payload=attack_payload,
                    base_system_prompt=campaign_config.target_system_prompt,
                    trace_id=result.trace.id,
                    rubric_name=campaign_config.rubric_name,
                )
            )
    finally:
        target.close()
    campaign.metadata["launch_readiness_replay"] = {
        "evidence_mode": "live_baseline_replay",
        "trace_ids": [
            result.trace.id for result in campaign.results if not result.verdict.is_jailbreak
        ],
        "scope_hash": hashlib.sha256(
            campaign_config.target_system_prompt.encode()
        ).hexdigest()[:16],
        "exploit_replay_passed": bool(validations) and all(
            item.exploit_replay_passed is True for item in validations
        ),
        "benign_passed": bool(validations) and all(
            item.benign_passed is True for item in validations
        ),
        "replay_cases": [
            {"case_id": case.case_id, "kind": case.kind, "passed": case.passed}
            for validation in validations
            for case in validation.replay_cases
        ],
    }


__all__ = ["attach_live_baseline_replay"]
