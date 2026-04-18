"""RedThreadEngine — campaign lifecycle facade."""

from __future__ import annotations

import logging

from redthread.config.settings import RedThreadSettings
from redthread.engine_telemetry import run_telemetry_pass
from redthread.engine_transcript import write_transcript
from redthread.models import CampaignConfig, CampaignResult
from redthread.orchestration.execution_truth_summary import build_execution_truth_summary
from redthread.orchestration.supervisor import RedThreadSupervisor
from redthread.pyrit_adapters.execution_context import capture_execution_records
from redthread.runtime_modes import campaign_runtime_mode, telemetry_runtime_mode
from redthread.tasks.base import Task, TaskType

logger = logging.getLogger(__name__)


class RedThreadEngine:
    """Facade over the LangGraph supervisor."""

    def __init__(self, settings: RedThreadSettings, trace_all: bool = False) -> None:
        self.settings = settings
        self._supervisor = RedThreadSupervisor(settings)
        settings.log_dir.mkdir(parents=True, exist_ok=True)
        settings.memory_dir.mkdir(parents=True, exist_ok=True)
        from redthread.observability.tracing import init_langsmith

        init_langsmith(settings, trace_all=trace_all)

    async def run(self, config: CampaignConfig) -> CampaignResult:
        campaign_task = Task.create(TaskType.CAMPAIGN)
        campaign_task.start()
        logger.info(
            "🚀 Campaign starting | objective=%s | algorithm=%s | personas=%d",
            config.objective,
            self.settings.algorithm.value,
            config.num_personas,
        )
        execution_records = []
        try:
            with capture_execution_records(execution_records):
                campaign = await self._supervisor.invoke(config)
                campaign.metadata.setdefault("runtime_mode", campaign_runtime_mode(self.settings))
                if self.settings.telemetry_enabled and not self.settings.dry_run:
                    await run_telemetry_pass(self.settings, campaign, config)
                elif self.settings.telemetry_enabled:
                    campaign.metadata["telemetry_mode"] = telemetry_runtime_mode(self.settings)
            self._attach_execution_truth(campaign, execution_records)
            campaign_task.complete(result={"asr": campaign.attack_success_rate})
            logger.info(
                "✅ Campaign complete | id=%s | ASR=%.1f%% | avg_score=%.2f | runs=%d",
                campaign.id,
                campaign.attack_success_rate * 100,
                campaign.average_score,
                len(campaign.results),
            )
            write_transcript(self.settings, campaign)
        except Exception as exc:
            campaign_task.fail(str(exc))
            logger.exception("💥 Campaign failed: %s", exc)
            raise
        return campaign

    def _attach_execution_truth(
        self,
        campaign: CampaignResult,
        execution_records: list,
    ) -> None:
        summary = build_execution_truth_summary(execution_records)
        campaign.metadata["execution_truth_summary"] = summary
        campaign.metadata["execution_records_sample"] = summary["record_sample"]
