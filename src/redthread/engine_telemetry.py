from __future__ import annotations

import logging

from redthread.config.settings import RedThreadSettings
from redthread.models import CampaignConfig, CampaignResult
from redthread.runtime_modes import telemetry_runtime_mode

logger = logging.getLogger(__name__)


async def run_telemetry_pass(
    settings: RedThreadSettings,
    campaign: CampaignResult,
    config: CampaignConfig,
) -> None:
    from redthread.pyrit_adapters.targets import build_target
    from redthread.telemetry.asi import AgentStabilityIndex
    from redthread.telemetry.collector import TelemetryCollector
    from redthread.telemetry.drift import DriftDetector

    logger.info("📡 Phase 5B | running post-campaign telemetry pass...")
    collector = TelemetryCollector(settings)
    target = build_target(settings)
    try:
        await collector.inject_canary_batch(target)
        drift_detector = DriftDetector(k_neighbors=5, distance_metric="cosine")
        baseline_embeddings = collector.storage.load_baseline()
        if baseline_embeddings:
            try:
                drift_detector.fit_baseline(baseline_embeddings)
            except Exception as exc:
                logger.warning("Failed to fit loaded drift baseline: %s", exc)
        report = AgentStabilityIndex(settings=settings, drift_detector=drift_detector).compute(collector)
        campaign.metadata["asi_report"] = report.model_dump(mode="json")
        campaign.metadata["telemetry_mode"] = telemetry_runtime_mode(settings)
        collector.export_jsonl(settings.log_dir / f"{campaign.id}_telemetry.jsonl")
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
