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
        """Delegate campaign execution to the LangGraph supervisor.

        Phase 5B: After the supervisor finishes, runs a post-campaign
        telemetry pass if settings.telemetry_enabled is True. This:
          1. Injects canary probes against the target
          2. Computes the ASI health report
          3. Attaches the report to CampaignResult.metadata
          4. Appends the ASI summary to the JSONL transcript
        """
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

            # ── Phase 5B: Post-campaign telemetry ────────────────────────────
            if self.settings.telemetry_enabled:
                await self._run_telemetry_pass(campaign, config)

        except Exception as exc:
            campaign_task.fail(str(exc))
            logger.exception("💥 Campaign failed: %s", exc)
            raise

        return campaign

    async def _run_telemetry_pass(
        self, campaign: CampaignResult, config: CampaignConfig
    ) -> None:
        """Phase 5B post-campaign diagnostic.

        Collects and embeds canary probes against the target, then
        computes the ASI health report. The report is attached to
        campaign.metadata and appended to the JSONL transcript.
        """
        from redthread.pyrit_adapters.targets import build_target
        from redthread.telemetry.asi import AgentStabilityIndex
        from redthread.telemetry.collector import TelemetryCollector

        logger.info("📡 Phase 5B | running post-campaign telemetry pass...")

        collector = TelemetryCollector(self.settings)
        target = build_target(self.settings)

        try:
            # Inject canary batch to populate the RC sub-score control group
            await collector.inject_canary_batch(target)

            # Load baseline for Semantic Drift if it exists
            from redthread.telemetry.drift import DriftDetector
            drift_detector = DriftDetector(k_neighbors=5, distance_metric="cosine")
            baseline_embeddings = collector.storage.load_baseline()
            if baseline_embeddings:
                try:
                    drift_detector.fit_baseline(baseline_embeddings)
                except Exception as exc:
                    logger.warning("Failed to fit loaded drift baseline: %s", exc)

            # Compute ASI report
            asi = AgentStabilityIndex(settings=self.settings, drift_detector=drift_detector)
            report = asi.compute(collector)

            # Attach report to campaign metadata (non-destructive)
            campaign.metadata["asi_report"] = report.model_dump(mode="json")

            # Append to JSONL transcript
            transcript_path = self.settings.log_dir / f"{campaign.id}.jsonl"
            with transcript_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "type": "asi_report",
                    "campaign_id": campaign.id,
                    "asi_score": report.overall_score,
                    "health_tier": report.health_tier,
                    "is_alert": report.is_alert,
                    "response_consistency": report.response_consistency,
                    "semantic_drift": report.semantic_drift,
                    "operational_health": report.operational_health,
                    "behavioral_stability": report.behavioral_stability,
                    "anomaly_count": sum(1 for a in report.anomalies if a.is_anomaly),
                    "recommendation": report.recommendation,
                }) + "\n")

            # Export raw telemetry to JSONL for validation
            tel_path = self.settings.log_dir / f"{campaign.id}_telemetry.jsonl"
            collector.export_jsonl(tel_path)

            logger.info(
                "📡 Phase 5B | ASI=%0.1f [%s] | alert=%s | %s",
                report.overall_score,
                report.health_tier,
                report.is_alert,
                report.recommendation,
            )

        except Exception as exc:
            logger.warning("📡 Phase 5B telemetry pass failed (non-critical): %s", exc)
        finally:
            target.close()


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
