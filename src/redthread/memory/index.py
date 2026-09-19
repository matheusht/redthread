"""Read/write interface for the append-only RedThread memory index."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path

from redthread.config.settings import RedThreadSettings
from redthread.core.defense_synthesis import DeploymentRecord
from redthread.memory.formatting import (
    HEADER,
    deserialize_deployment_record,
    format_entry,
)
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
        if self._is_duplicate(record.trace_id):
            logger.debug("MemoryIndex: duplicate trace_id=%s — skipping.", record.trace_id)
            return False
        record.metadata = {
            **record.metadata,
            "guardrail_status": guardrail_status,
            "active_guardrail": guardrail_status == "active_guardrail",
        }
        if not self._is_duplicate_clause(record):
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(format_entry(record))
        else:
            logger.debug(
                "MemoryIndex: duplicate clause for %s — skipped MEMORY.md write", record.trace_id
            )
        with self._deployments_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record)) + "\n")
        logger.info(
            "📚 MemoryIndex updated | trace=%s | category=%s",
            record.trace_id,
            record.classification.category,
        )
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
        return self._path.read_text(encoding="utf-8") if self._path.exists() else ""

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
        if not self._deployments_path.exists():
            return []
        return [
            self._deserialize(line)
            for line in self._deployments_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def deployments_by_trace_ids(self, trace_ids: Iterable[str]) -> list[DeploymentRecord]:
        wanted = set(trace_ids)
        if not wanted:
            return []
        return [record for record in self.iter_deployments() if record.trace_id in wanted]

    def load_scoped_guardrail_records(
        self, target_model: str, prompt_hash: str
    ) -> list[DeploymentRecord]:
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

        def _dedup(items: Iterable[str]) -> list[str]:
            seen: set[str] = set()
            out: list[str] = []
            for item in items:
                norm = " ".join(item.lower().split())
                if norm not in seen:
                    seen.add(norm)
                    out.append(item)
            return out

        deployments = self.iter_deployments()
        if deployments:
            return _dedup(
                r.guardrail_clause
                for r in self.load_scoped_guardrail_records(target_model, prompt_hash)
            )
        clauses: list[str] = []
        for block in self.all_entries_raw().split("---\n\n"):
            if (
                "✅ YES" in block
                and f"model=`{target_model}` | prompt_hash=`{prompt_hash}`" in block
            ):
                for line in block.splitlines():
                    if line.startswith("> **Guardrail clause:**"):
                        clauses.append(line.replace("> **Guardrail clause:**", "").strip())
                        break
        return _dedup(clauses)

    def _ensure_files(self) -> None:
        if not self._path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(HEADER, encoding="utf-8")
        if not self._deployments_path.exists():
            self._deployments_path.touch()

    def _deserialize(self, line: str) -> DeploymentRecord:
        return deserialize_deployment_record(line)

    def _is_duplicate(self, trace_id: str) -> bool:
        return trace_id in self.known_trace_ids()

    def _is_duplicate_clause(self, record: DeploymentRecord) -> bool:
        norm_incoming = " ".join(record.guardrail_clause.lower().split())
        if not norm_incoming:
            return False
        existing = self.load_scoped_guardrails(
            record.target_model, record.target_system_prompt_hash
        )
        return any(" ".join(c.lower().split()) == norm_incoming for c in existing)
