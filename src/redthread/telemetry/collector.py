"""TelemetryCollector — Phase 5B: Active probe with canary injection.

Moves from a passive log recorder to an active probe that:
  1. Wraps every RedThreadTarget.send() to capture operational metrics
  2. Periodically injects deterministic canary prompts for Response Consistency
  3. Computes and caches response embeddings for Semantic Drift tracking
  4. Exports records to JSONL for historical validation

Anti-Hallucination SOP Gap G4: The collector now has an active canary injection
mechanism that injects 3-5 standardized benign prompts at configurable intervals.
This gives the Response Consistency sub-score a noise-free control group signal.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

from redthread.config.settings import RedThreadSettings
from redthread.telemetry.models import TelemetryRecord
from redthread.telemetry.storage import TelemetryStorage

logger = logging.getLogger(__name__)


# ── Canary Prompt Registry ────────────────────────────────────────────────────
# Deterministic, benign, semantically stable probes. These are injected
# periodically to provide a noise-free consistency control group.
# Every canary has an immutable ID so we can group responses over time.

CANARY_PROMPTS: dict[str, str] = {
    "canary-001": "What is today's date?",
    "canary-002": "Please summarize what you can help me with in one sentence.",
    "canary-003": "What is 2 + 2?",
    "canary-004": "Repeat the word 'hello' exactly once.",
    "canary-005": "What is the capital of France?",
}


def _hash_prompt(prompt: str) -> str:
    """Compute a short SHA-256 prefix for prompt identity tracking."""
    return hashlib.sha256(prompt.encode()).hexdigest()[:16]


def _estimate_tokens(text: str) -> int:
    """Fast token count estimate (4 chars ≈ 1 token, no tiktoken import needed)."""
    return max(1, len(text) // 4)


class TelemetryCollector:
    """Active telemetry probe for Phase 5B.

    Usage::

        collector = TelemetryCollector(settings)

        # Wrap a target call:
        start = time.monotonic()
        response = await target.send(prompt)
        latency_ms = (time.monotonic() - start) * 1000
        await collector.record_interaction(prompt, response, latency_ms)

        # Inject canary batch (call once per monitoring cycle):
        canary_records = await collector.inject_canary_batch(target)

        # Get metric series for ARIMA:
        latencies = collector.get_metric_series("latency_ms")
    """

    def __init__(self, settings: RedThreadSettings) -> None:
        self.settings = settings
        self.storage = TelemetryStorage(settings)
        self._canary_injection_count = 0
        self._canary_interval = 10  # Inject canaries every N organic interactions

    async def record_interaction(
        self,
        prompt: str,
        response: str,
        latency_ms: float,
        error: bool = False,
        error_type: str = "",
        is_canary: bool = False,
        canary_id: str = "",
    ) -> TelemetryRecord:
        """Record a single interaction and compute its response embedding.

        Embeddings are computed lazily from the EmbeddingClient; in dry_run
        mode the client returns deterministic random vectors.
        """
        from redthread.telemetry.embeddings import EmbeddingClient

        embedding: list[float] = []
        try:
            client = EmbeddingClient(self.settings)
            embedding = await client.embed(response)
        except Exception as exc:
            logger.warning("Embedding failed for record, skipping: %s", exc)

        record = TelemetryRecord(
            target_model=self.settings.target_model,
            prompt_hash=_hash_prompt(prompt),
            latency_ms=latency_ms,
            input_tokens=_estimate_tokens(prompt),
            output_tokens=_estimate_tokens(response),
            error=error,
            error_type=error_type,
            response_text=response,
            response_embedding=embedding,
            is_canary=is_canary,
            canary_id=canary_id,
        )

        self.storage.insert(record)
        self._canary_injection_count += 1 if not is_canary else 0

        logger.debug(
            "📊 TelemetryCollector | recorded | latency=%.1fms | tokens_out=%d | canary=%s",
            latency_ms,
            record.output_tokens,
            is_canary,
        )
        return record

    async def inject_canary_batch(self, target: Any) -> list[TelemetryRecord]:
        """Send all CANARY_PROMPTS to the target and record the results.

        This provides the noise-free control group for Response Consistency (RC).
        Each canary has a stable ID allowing variance to be measured over time.

        Args:
            target: A RedThreadTarget (or any object with an async .send() method)

        Returns:
            List of TelemetryRecord for each canary interaction.
        """
        canary_records: list[TelemetryRecord] = []

        logger.info("🐦 TelemetryCollector | injecting %d canary probes...", len(CANARY_PROMPTS))

        for canary_id, canary_prompt in CANARY_PROMPTS.items():
            start = time.monotonic()
            error = False
            error_type = ""
            response = ""

            try:
                response = await target.send(
                    prompt=canary_prompt,
                    conversation_id=f"canary-{canary_id}",
                )
            except Exception as exc:
                error = True
                error_type = type(exc).__name__
                response = f"[ERROR: {exc}]"
                logger.warning("Canary %s failed: %s", canary_id, exc)

            latency_ms = (time.monotonic() - start) * 1000

            record = await self.record_interaction(
                prompt=canary_prompt,
                response=response,
                latency_ms=latency_ms,
                error=error,
                error_type=error_type,
                is_canary=True,
                canary_id=canary_id,
            )
            canary_records.append(record)

        logger.info(
            "🐦 TelemetryCollector | canary batch complete | %d records",
            len(canary_records),
        )
        return canary_records

    def should_inject_canaries(self) -> bool:
        """Return True if it is time to inject a canary batch.

        Injects once every `_canary_interval` organic interactions.
        Always injects if no canaries have been recorded yet.
        """
        canary_count = self.storage.get_total_canary_records()
        if canary_count == 0:
            return True
        return self._canary_injection_count >= self._canary_interval

    def reset_canary_counter(self) -> None:
        """Reset the organic interaction counter after canary injection."""
        self._canary_injection_count = 0

    def get_metric_series(
        self,
        metric: str,
        window: int | None = None,
        organic_only: bool = True,
    ) -> list[float]:
        """Extract a time-ordered series of a single metric from records."""
        return self.storage.get_metric_series(metric, window, organic_only)

    def get_canary_records(self, canary_id: str | None = None) -> list[TelemetryRecord]:
        """Return all canary records, optionally filtered by canary_id."""
        return self.storage.get_canary_records(canary_id)

    def get_organic_records(self, window: int | None = None) -> list[TelemetryRecord]:
        """Return organic (non-canary) records, optionally windowed."""
        return self.storage.get_organic_records(window)

    @property
    def total_records(self) -> int:
        return self.storage.get_total_records()

    @property
    def total_canary_records(self) -> int:
        return self.storage.get_total_canary_records()

    def export_jsonl(self, path: Path) -> None:
        """Persist all telemetry records to a JSONL file for historical validation."""
        path.parent.mkdir(parents=True, exist_ok=True)
        # We fetch all records just to export. In production an incremental approach might be better.
        records = self.storage.get_organic_records() + self.storage.get_canary_records()
        with path.open("w", encoding="utf-8") as f:
            for record in records:
                # Omit the full embedding vector from JSONL (too large)
                data = record.model_dump(mode="json")
                data["response_embedding"] = f"[dim={len(record.response_embedding)}]"
                f.write(json.dumps(data) + "\n")
        logger.info(
            "📝 TelemetryCollector | exported %d records to %s",
            len(records),
            path,
        )
