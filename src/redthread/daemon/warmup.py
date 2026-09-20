"""Drift baseline bootstrapping and warmup for SecurityGuardDaemon."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any

from redthread.pyrit_adapters.targets import (
    ExecutionMetadata,
    send_with_execution_metadata,
)
from redthread.telemetry.collector import TelemetryCollector
from redthread.telemetry.drift import DriftDetector
from redthread.telemetry.prompts import CANARY_PROMPTS

logger = logging.getLogger(__name__)


async def bootstrap_drift_baseline(
    collector: TelemetryCollector, target: Any, probe_count: int = 10
) -> DriftDetector:
    """Bootstrap the drift baseline if it doesn't exist."""
    drift_detector = DriftDetector(k_neighbors=5, distance_metric="cosine")
    baseline = collector.storage.load_baseline()
    if baseline:
        logger.info("🛡️ Daemon | loaded existing drift baseline (N=%d)", len(baseline))
        drift_detector.fit_baseline(baseline)
        return drift_detector

    logger.info(
        "🛡️ Daemon | no drift baseline found, initiating warmup (%d probes)", probe_count
    )
    baseline_embeddings = []
    prompts = sorted(CANARY_PROMPTS.values())

    for i in range(probe_count):
        prompt = random.choice(prompts)
        try:
            start_t = time.monotonic()
            response = await send_with_execution_metadata(
                target,
                prompt=prompt,
                conversation_id=f"warmup-{i}",
                execution_metadata=ExecutionMetadata(
                    seam="telemetry.warmup",
                    role="telemetry",
                    evidence_class="telemetry_signal",
                ),
            )
            lat = (time.monotonic() - start_t) * 1000
            record = await collector.record_interaction(
                prompt=prompt,
                response=response,
                latency_ms=lat,
                is_canary=True,
                canary_id=f"warmup-{i}",
            )
            if record.response_embedding:
                baseline_embeddings.append(record.response_embedding)
        except Exception as exc:
            logger.warning("Warmup probe %d failed: %s", i, exc)
        await asyncio.sleep(1.0)

    if baseline_embeddings:
        collector.storage.save_baseline(baseline_embeddings)
        drift_detector.fit_baseline(baseline_embeddings)
        logger.info(
            "🛡️ Daemon | warmup complete, computed new baseline (N=%d)",
            len(baseline_embeddings),
        )
    else:
        logger.warning("🛡️ Daemon | warmup failed to collect embeddings")
    return drift_detector
