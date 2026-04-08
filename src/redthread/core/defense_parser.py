"""Parser helpers for defense synthesis outputs."""

from __future__ import annotations

from redthread.core.defense_models import VulnerabilityClassification


def parse_architect_output(raw: str) -> tuple[VulnerabilityClassification, str, str]:
    """Parse the Defense Architect's structured output."""

    def extract(key: str) -> str:
        for line in raw.splitlines():
            if line.startswith(f"{key}:"):
                return line[len(key) + 1 :].strip()
        return ""

    classification = VulnerabilityClassification(
        category=extract("CATEGORY") or "unknown",
        owasp_ref=extract("OWASP_REF") or "LLM01",
        mitre_atlas_ref=extract("MITRE_ATLAS_REF") or "AML.T0054",
        severity=extract("SEVERITY") or "HIGH",
        attack_vector=extract("ATTACK_VECTOR") or "",
    )
    clause = extract("GUARDRAIL_CLAUSE")
    rationale = extract("RATIONALE")
    return classification, clause, rationale


__all__ = ["parse_architect_output"]
