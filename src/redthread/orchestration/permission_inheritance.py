"""Permission inheritance checks for agentic-security execution paths."""

from __future__ import annotations

from redthread.orchestration.models import ProvenanceRecord
from redthread.tools.authorization.capabilities import is_high_risk_capability


def violates_permission_inheritance(
    provenance: ProvenanceRecord,
    capability: str,
) -> bool:
    return provenance.has_untrusted_lineage and is_high_risk_capability(capability)
