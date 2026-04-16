"""Permission inheritance checks for agentic-security execution paths."""

from __future__ import annotations

from redthread.orchestration.models import ProvenanceRecord


HIGH_RISK_CAPABILITIES = {"shell.exec", "db.export", "db.write", "http.post"}


def violates_permission_inheritance(
    provenance: ProvenanceRecord,
    capability: str,
) -> bool:
    return provenance.derived_from_untrusted and capability in HIGH_RISK_CAPABILITIES
