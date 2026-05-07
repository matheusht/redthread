"""JSON import helpers for weak external evidence bundles."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from redthread.reporting.external_evidence import (
    ExternalEvidenceBundle,
    ExternalEvidenceItem,
    ExternalEvidenceSource,
    garak_result_to_evidence,
    promptfoo_result_to_evidence,
    strix_finding_to_evidence,
)
from redthread.reporting.public_artifacts import prompt_safe_json

Mapper = Callable[[dict[str, Any]], ExternalEvidenceItem]

_MAPPERS: dict[ExternalEvidenceSource, Mapper] = {
    ExternalEvidenceSource.PROMPTFOO: promptfoo_result_to_evidence,
    ExternalEvidenceSource.GARAK: garak_result_to_evidence,
    ExternalEvidenceSource.STRIX: strix_finding_to_evidence,
}


def import_external_evidence_file(
    input_path: Path,
    *,
    source: ExternalEvidenceSource,
    output_path: Path,
) -> ExternalEvidenceBundle:
    """Import raw external rows as weak evidence and write bundle JSON."""
    bundle = external_evidence_from_payload(_read_json(input_path), source=source)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_bundle_to_json(bundle), encoding="utf-8")
    return bundle


def external_evidence_from_payload(
    payload: object,
    *,
    source: ExternalEvidenceSource,
) -> ExternalEvidenceBundle:
    """Build a weak evidence bundle from common JSON payload shapes."""
    if isinstance(payload, Mapping) and payload.get("schema_version") == "redthread.external_evidence_bundle.v1":
        return ExternalEvidenceBundle.model_validate(payload)
    rows = _extract_rows(payload)
    mapper = _MAPPERS.get(source)
    items = [_generic_item(source, row) if mapper is None else mapper(row) for row in rows]
    return ExternalEvidenceBundle(source=source, items=items)


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _bundle_to_json(bundle: ExternalEvidenceBundle) -> str:
    return prompt_safe_json(bundle.model_dump(mode="json"))


def _extract_rows(payload: object) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [_ensure_mapping(row) for row in payload]
    if isinstance(payload, Mapping):
        for key in ("results", "findings", "items", "rows"):
            raw_rows = payload.get(key)
            if isinstance(raw_rows, list):
                return [_ensure_mapping(row) for row in raw_rows]
        return [_ensure_mapping(payload)]
    msg = "external evidence input must be a JSON object or list"
    raise ValueError(msg)


def _ensure_mapping(row: object) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        msg = "external evidence rows must be JSON objects"
        raise ValueError(msg)
    return dict(row)


def _generic_item(source: ExternalEvidenceSource, row: dict[str, Any]) -> ExternalEvidenceItem:
    item_data = {key: value for key, value in row.items() if key not in {"source", "raw"}}
    item_data.setdefault("source_id", str(row.get("id", "generic-evidence")))
    item_data.setdefault("title", str(row.get("description", "generic imported evidence")))
    return ExternalEvidenceItem(source=source, raw=row, **item_data)


__all__ = ["external_evidence_from_payload", "import_external_evidence_file"]
