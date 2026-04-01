"""RedThreadEngine — Campaign lifecycle facade (Phase 4).

Phase 4 refactor: this module is now a strict facade over the LangGraph supervisor.
All orchestration logic (persona generation, parallel attack fan-out, G-Eval judging,
and defense synthesis) lives in `orchestration/supervisor.py`.

This module only:
  1. Initialises the SupervisorGraph with the provided settings.
  2. Calls supervisor.invoke(config).
  3. Writes the JSONL transcript.
  4. Returns CampaignResult.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from redthread.config.settings import RedThreadSettings
from redthread.models import CampaignConfig, CampaignResult
from redthread.orchestration.supervisor import RedThreadSupervisor
from redthread.tasks.base import Task, TaskType

logger = logging.getLogger(__name__)


class RedThreadEngine:
    """Facade over the LangGraph supervisor — Phase 4 orchestration entry point.

    Usage::

        engine = RedThreadEngine(settings)
        result = await engine.run(config)
    """

    def __init__(self, settings: RedThreadSettings) -> None:
        self.settings = settings
        self._supervisor = RedThreadSupervisor(settings)
        settings.log_dir.mkdir(parents=True, exist_ok=True)
        settings.memory_dir.mkdir(parents=True, exist_ok=True)

    async def run(self, config: CampaignConfig) -> CampaignResult:
        """Delegate campaign execution to the LangGraph supervisor."""

        campaign_task = Task.create(TaskType.CAMPAIGN)
        campaign_task.start()

        logger.info(
            "🚀 Campaign starting | objective=%s | algorithm=%s | personas=%d",
            config.objective,
            self.settings.algorithm.value,
            config.num_personas,
        )

        try:
            campaign = await self._supervisor.invoke(config)

            campaign_task.complete(result={"asr": campaign.attack_success_rate})

            logger.info(
                "✅ Campaign complete | id=%s | ASR=%.1f%% | avg_score=%.2f | runs=%d",
                campaign.id,
                campaign.attack_success_rate * 100,
                campaign.average_score,
                len(campaign.results),
            )

            self._write_transcript(campaign)

        except Exception as exc:
            campaign_task.fail(str(exc))
            logger.exception("💥 Campaign failed: %s", exc)
            raise

        return campaign

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
                
                if result.trace.nodes:
                    line["tree_stats"] = {
                        "total_nodes": len(result.trace.nodes),
                        "pruned_nodes": sum(1 for n in result.trace.nodes if n.is_pruned),
                        "max_depth_reached": max((n.depth for n in result.trace.nodes), default=0),
                    }
                    line["winning_path"] = [
                        {"depth": n.depth, "prompt": n.attacker_prompt[:150], "score": n.score}
                        for n in result.trace.nodes if not n.is_pruned
                    ]
                    
                f.write(json.dumps(line) + "\n")

        logger.info("📝 Transcript written to %s", transcript_path)
