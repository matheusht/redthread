"""Read/write interface for the append-only RedThread memory index."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path

from redthread.config.settings import RedThreadSettings
from redthread.core.defense_models import BenignValidationCheck, ReplayCaseResult
from redthread.core.defense_reporting_models import DefenseValidationReport
from redthread.core.defense_synthesis import (
    DeploymentRecord,
    ValidationResult,
    VulnerabilityClassification,
)
from redthread.memory.file_locks import locked_append, locked_path
from redthread.memory.formatting import HEADER, format_entry
from redthread.memory.legacy_parser import load_legacy_guardrails
from redthread.orchestration.canary_containment import evaluate_canary_containment

logger = logging.getLogger(__name__)

_MEMORY_FILENAME = "MEMORY.md"
_DEPLOYMENTS_FILENAME = "deployments.jsonl"


class MemoryIndex:
    """Access append-only markdown and JSONL deployment records."""

    def __init__(self, settings: RedThreadSettings) -> None:
        self._settings = settings
        self._path: Path = settings.memory_dir / _MEMORY_FILENAME
        self._deployments_path: Path = settings.memory_dir / _DEPLOYMENTS_FILENAME
        self._ensure_files()

    def append(self, record: DeploymentRecord, guardrail_status: str = "active_guardrail") -> bool:
        """Append a guardrail record unless its trace ID already exists.

        `active_guardrail` records may be loaded for runtime injection. Defense
        synthesis writes `validated_candidate` records until explicit promotion.
        """
        canary_decision = evaluate_canary_containment(
            seam="memory.write",
            prompt=f"{record.guardrail_clause}\n{record.validation.replay_response}",
            metadata=record.metadata,
            mode=self._settings_canary_policy(),
        )
        if canary_decision.blocked:
            logger.warning(
                "MemoryIndex blocked canary-tagged write | trace=%s | tags=%s",
                record.trace_id,
                canary_decision.canary_tags,
            )
            return False
        with locked_append(self._deployments_path) as deployments_handle:
            if self._is_duplicate(record.trace_id):
                logger.debug("MemoryIndex: duplicate trace_id=%s — skipping.", record.trace_id)
                return False
            record.metadata = {
                **record.metadata,
                "guardrail_status": guardrail_status,
                "active_guardrail": guardrail_status == "active_guardrail",
            }
            with locked_append(self._path) as handle:
                handle.write(format_entry(record))
            deployments_handle.write(json.dumps(asdict(record)) + "\n")
        logger.info("📚 MemoryIndex updated | trace=%s | category=%s", record.trace_id, record.classification.category)
        return True

    def _settings_canary_policy(self) -> str:
        return self._settings.canary_policy_preset.value

    def append_records(
        self,
        records: Iterable[DeploymentRecord],
        guardrail_status: str = "active_guardrail",
    ) -> list[str]:
        """Append a bounded batch and return the trace IDs written this time."""
        written: list[str] = []
        for record in records:
            if self.append(record, guardrail_status=guardrail_status):
                written.append(record.trace_id)
        return written

    def all_entries_raw(self) -> str:
        with locked_path(self._path):
            return self._all_entries_raw_unlocked()

    def known_trace_ids(self) -> list[str]:
        deployments = self.iter_deployments()
        if deployments:
            return [record.trace_id for record in deployments]
        return [
            line.replace("**Trace:**", "").strip().strip("`")
            for line in self.all_entries_raw().splitlines()
            if line.startswith("**Trace:**")
        ]

    def iter_deployments(self) -> list[DeploymentRecord]:
        with locked_path(self._deployments_path):
            return self._iter_deployments_unlocked()

    def deployments_by_trace_ids(self, trace_ids: Iterable[str]) -> list[DeploymentRecord]:
        wanted = set(trace_ids)
        if not wanted:
            return []
        return [record for record in self.iter_deployments() if record.trace_id in wanted]

    def load_scoped_guardrail_records(self, target_model: str, prompt_hash: str) -> list[DeploymentRecord]:
        """Load active structured guardrail records for one target scope."""
        return [
            record
            for record in self.iter_deployments()
            if record.target_model == target_model
            and record.target_system_prompt_hash == prompt_hash
            and record.validation.passed
            and record.metadata.get("guardrail_status", "active_guardrail") == "active_guardrail"
        ]

    def load_scoped_guardrails(self, target_model: str, prompt_hash: str) -> list[str]:
        """Load active guardrail clauses for one target scope.

        Structured deployment records are authoritative when present. Markdown is
        only a backward-compatible fallback for legacy memory files.
        """
        deployments = self.iter_deployments()
        if deployments:
            return [record.guardrail_clause for record in self.load_scoped_guardrail_records(target_model, prompt_hash)]
        return load_legacy_guardrails(self.all_entries_raw(), target_model, prompt_hash)

    def _ensure_files(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with locked_append(self._path) as handle:
            if self._path.stat().st_size == 0:
                handle.write(HEADER)
        with locked_append(self._deployments_path):
            pass

    def _deserialize(self, line: str) -> DeploymentRecord:
        payload = json.loads(line)
        validation_payload = payload["validation"]
        benign_checks = [
            BenignValidationCheck(**check)
            for check in validation_payload.get("benign_checks", [])
        ]
        replay_cases = [
            ReplayCaseResult(**case)
            for case in validation_payload.get("replay_cases", [])
        ]
        report_payload = payload.get("validation_report")
        return DeploymentRecord(
            trace_id=payload["trace_id"],
            guardrail_clause=payload["guardrail_clause"],
            classification=VulnerabilityClassification(**payload["classification"]),
            validation=ValidationResult(
                **{
                    **validation_payload,
                    "benign_checks": benign_checks,
                    "replay_cases": replay_cases,
                }
            ),
            target_model=payload["target_model"],
            target_system_prompt_hash=payload["target_system_prompt_hash"],
            validation_report=DefenseValidationReport(**report_payload) if report_payload else None,
            metadata=payload.get("metadata", {}),
        )

    def _is_duplicate(self, trace_id: str) -> bool:
        deployments = self._iter_deployments_unlocked()
        if deployments:
            return trace_id in {record.trace_id for record in deployments}
        return any(
            line.replace("**Trace:**", "").strip().strip("`") == trace_id
            for line in self._all_entries_raw_unlocked().splitlines()
            if line.startswith("**Trace:**")
        )

    def _all_entries_raw_unlocked(self) -> str:
        return self._path.read_text(encoding="utf-8") if self._path.exists() else ""

    def _iter_deployments_unlocked(self) -> list[DeploymentRecord]:
        if not self._deployments_path.exists():
            return []
        return [
            self._deserialize(line)
            for line in self._deployments_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
