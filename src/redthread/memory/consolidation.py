"""Memory Consolidation — "Dream" background job for cross-session knowledge.

Scans campaign JSONL transcript logs in `settings.log_dir`, identifies
successful attack traces not yet in MEMORY.md, synthesizes defenses for
them offline, and persists the results to the index.

This is designed to run as a background task after campaign completion,
or as a standalone CLI command (`redthread consolidate`).

Pattern: Claude Code "Dream" — offline replay and learning from past runs.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from redthread.config.settings import RedThreadSettings

logger = logging.getLogger(__name__)


@dataclass
class ConsolidationReport:
    """Summary of a single consolidation run."""

    scanned_files: int
    new_jailbreaks_found: int
    defenses_synthesized: int
    defenses_validated: int
    skipped_duplicates: int
    errors: list[str]


class DreamConsolidator:
    """Offline consolidation job — reads logs, synthesizes missing defenses.

    Usage::

        consolidator = DreamConsolidator(settings)
        report = await consolidator.run()
        print(f"Synthesized {report.defenses_synthesized} new guardrails.")
    """

    def __init__(self, settings: RedThreadSettings) -> None:
        self.settings = settings

    async def run(self) -> ConsolidationReport:
        """Scan logs and synthesize defenses for any un-indexed jailbreaks."""
        from redthread.core.defense_synthesis import DefenseSynthesisEngine
        from redthread.memory.index import MemoryIndex

        index = MemoryIndex(self.settings)
        known_trace_ids = set(index.known_trace_ids())
        engine = DefenseSynthesisEngine(self.settings)

        report = ConsolidationReport(
            scanned_files=0,
            new_jailbreaks_found=0,
            defenses_synthesized=0,
            defenses_validated=0,
            skipped_duplicates=0,
            errors=[],
        )

        log_dir = self.settings.log_dir
        jsonl_files = sorted(log_dir.glob("*.jsonl"))

        logger.info(
            "💤 Dream consolidation starting | scanning %d log files in %s",
            len(jsonl_files),
            log_dir,
        )

        for log_file in jsonl_files:
            report.scanned_files += 1
            jailbreak_results = self._extract_jailbreaks(log_file, known_trace_ids)

            for attack_result in jailbreak_results:
                report.new_jailbreaks_found += 1

                # Skip if already indexed
                if attack_result.trace.id in known_trace_ids:
                    report.skipped_duplicates += 1
                    continue

                try:
                    record = await engine.run(attack_result)
                    report.defenses_synthesized += 1

                    if record.validation.passed:
                        written = index.append(record)
                        if written:
                            known_trace_ids.add(attack_result.trace.id)
                            report.defenses_validated += 1
                            logger.info(
                                "✅ Defense indexed | trace=%s | category=%s",
                                record.trace_id,
                                record.classification.category,
                            )
                    else:
                        logger.warning(
                            "⚠️  Defense validation failed | trace=%s | score=%.2f",
                            record.trace_id,
                            record.validation.judge_score,
                        )

                except Exception as exc:
                    err_msg = f"Failed to synthesize defense for trace in {log_file.name}: {exc}"
                    report.errors.append(err_msg)
                    logger.exception(err_msg)

        logger.info(
            "💤 Dream consolidation complete | scanned=%d | found=%d | "
            "synthesized=%d | validated=%d | errors=%d",
            report.scanned_files,
            report.new_jailbreaks_found,
            report.defenses_synthesized,
            report.defenses_validated,
            len(report.errors),
        )

        return report

    def _extract_jailbreaks(
        self,
        log_file: Path,
        known_trace_ids: set[str],
    ) -> list:
        """Parse a JSONL transcript and return AttackResult objects for confirmed jailbreaks."""
        from redthread.models import AttackResult

        results = []
        try:
            with log_file.open("r", encoding="utf-8") as f:
                for raw_line in f:
                    raw_line = raw_line.strip()
                    if not raw_line:
                        continue
                    try:
                        entry = json.loads(raw_line)
                    except json.JSONDecodeError:
                        continue

                    # Only process attack_result lines with confirmed jailbreaks
                    if (
                        entry.get("type") == "attack_result"
                        and entry.get("is_jailbreak") is True
                    ):
                        # Re-hydrate from raw log data if full model data included
                        if "full_result" in entry:
                            try:
                                result = AttackResult.model_validate(entry["full_result"])
                                if result.trace.id not in known_trace_ids:
                                    results.append(result)
                            except Exception:
                                pass  # Silently skip malformed entries

        except OSError as exc:
            logger.error("Failed to read log file %s: %s", log_file, exc)

        return results
