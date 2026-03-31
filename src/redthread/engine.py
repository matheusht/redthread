"""RedThreadEngine — Campaign lifecycle orchestrator.

Analog of Claude Code's QueryEngine. Owns the full lifecycle of a red-team campaign:
  1. Create campaign task
  2. Generate adversarial personas  
  3. Run attack algorithm against each persona
  4. Collect + score results
  5. Write JSONL transcript
  6. Return CampaignResult
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from redthread.config.settings import AlgorithmType, RedThreadSettings
from redthread.core.pair import PAIRAttack
from redthread.models import CampaignConfig, CampaignResult
from redthread.personas.generator import PersonaGenerator
from redthread.tasks.base import Task, TaskType

logger = logging.getLogger(__name__)


class RedThreadEngine:
    """Orchestrates a complete red-team campaign.

    Usage:
        engine = RedThreadEngine(settings)
        result = await engine.run(config)
    """

    def __init__(self, settings: RedThreadSettings) -> None:
        self.settings = settings
        self._persona_gen = PersonaGenerator(settings)
        settings.log_dir.mkdir(parents=True, exist_ok=True)
        settings.memory_dir.mkdir(parents=True, exist_ok=True)

    async def run(self, config: CampaignConfig) -> CampaignResult:
        """Execute a full red-team campaign."""

        campaign_task = Task.create(TaskType.CAMPAIGN)
        campaign_task.start()

        logger.info(
            "🚀 Campaign starting | id=%s | objective=%s | algorithm=%s",
            campaign_task.id,
            config.objective,
            self.settings.algorithm,
        )

        campaign = CampaignResult(config=config, started_at=datetime.now(timezone.utc))

        try:
            # Phase 1: Generate personas
            logger.info("👤 Generating %d adversarial personas...", config.num_personas)
            personas = await self._persona_gen.generate_batch(
                objective=config.objective,
                count=config.num_personas,
            )

            # Phase 2: Execute attacks
            for i, persona in enumerate(personas, 1):
                logger.info(
                    "⚔️  Running attack %d/%d | persona=%s | tactic=%s",
                    i,
                    config.num_personas,
                    persona.name,
                    persona.tactic.value,
                )

                attack_task = Task.create(TaskType.ATTACK_RUN)
                attack_task.start()

                try:
                    result = await self._run_algorithm(persona, config)
                    campaign.results.append(result)
                    attack_task.complete(result=result.trace.outcome.value)

                    logger.info(
                        "📊 Attack complete | outcome=%s | score=%.2f | iterations=%d",
                        result.trace.outcome.value,
                        result.verdict.score,
                        result.iterations_used,
                    )

                except Exception as exc:
                    attack_task.fail(str(exc))
                    logger.exception("❌ Attack run failed for persona %s", persona.name)

            # Phase 3: Finalize campaign
            campaign.ended_at = datetime.now(timezone.utc)
            campaign_task.complete(result={"asr": campaign.attack_success_rate})

            logger.info(
                "✅ Campaign complete | id=%s | ASR=%.1f%% | avg_score=%.2f | runs=%d",
                campaign.id,
                campaign.attack_success_rate * 100,
                campaign.average_score,
                len(campaign.results),
            )

            # Write JSONL transcript
            self._write_transcript(campaign)

        except Exception as exc:
            campaign_task.fail(str(exc))
            logger.exception("💥 Campaign failed: %s", exc)
            raise

        return campaign

    async def _run_algorithm(
        self,
        persona: "Persona",  # type: ignore[name-defined]  # noqa: F821
        config: CampaignConfig,
    ) -> "AttackResult":  # type: ignore[name-defined]  # noqa: F821
        """Dispatch to the configured attack algorithm."""

        if self.settings.algorithm == AlgorithmType.PAIR:
            attacker = PAIRAttack(self.settings)
            return await attacker.run(persona, rubric_name=config.rubric_name)

        # TAP/Crescendo/MCTS deferred to Phase 3
        raise NotImplementedError(
            f"Algorithm '{self.settings.algorithm}' not yet implemented. "
            "Currently only PAIR is available (Phase 2). "
            "TAP, Crescendo, and MCTS are coming in Phase 3."
        )

    def _write_transcript(self, campaign: CampaignResult) -> None:
        """Write campaign results to an append-only JSONL transcript."""
        transcript_path = self.settings.log_dir / f"{campaign.id}.jsonl"

        with transcript_path.open("w", encoding="utf-8") as f:
            # Write summary line
            summary = {
                "type": "campaign_result",
                "id": campaign.id,
                "objective": campaign.config.objective,
                "algorithm": self.settings.algorithm.value,
                "target_model": self.settings.target_model,
                "attacker_model": self.settings.attacker_model,
                "judge_model": self.settings.judge_model,
                "num_runs": len(campaign.results),
                "attack_success_rate": campaign.attack_success_rate,
                "average_score": campaign.average_score,
                "started_at": campaign.started_at.isoformat(),
                "ended_at": campaign.ended_at.isoformat() if campaign.ended_at else None,
            }
            f.write(json.dumps(summary) + "\n")

            # Write each result as a line
            for result in campaign.results:
                line = {
                    "type": "attack_result",
                    "result_id": result.id,
                    "persona_name": result.trace.persona.name,
                    "tactic": result.trace.persona.tactic.value,
                    "outcome": result.trace.outcome.value,
                    "score": result.verdict.score,
                    "is_jailbreak": result.verdict.is_jailbreak,
                    "iterations": result.iterations_used,
                    "duration_seconds": result.duration_seconds,
                    "reasoning": result.verdict.reasoning,
                    "feedback": result.verdict.feedback,
                    "turns": [
                        {
                            "turn": t.turn_number,
                            "attacker": t.attacker_prompt[:200],
                            "target": t.target_response[:200],
                            "improvement": t.improvement_rationale,
                        }
                        for t in result.trace.turns
                    ],
                }
                f.write(json.dumps(line) + "\n")

        logger.info("📝 Transcript written to %s", transcript_path)
