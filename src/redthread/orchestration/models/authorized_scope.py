"""Authorized scope contracts for safe campaign planning."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AuthorizedScope(BaseModel):
    """Structured boundary for what a RedThread campaign may touch."""

    target_ids: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    denied_tools: list[str] = Field(default_factory=list)
    allowed_domains: list[str] = Field(default_factory=list)
    denied_domains: list[str] = Field(default_factory=list)
    workspace_roots: list[str] = Field(default_factory=list)
    can_use_network: bool = False
    can_execute_code: bool = False
    evidence_retention_policy: str = "campaign_output_only"
    user_text_cannot_expand_scope: bool = True

    def allows_target(self, target_id: str) -> bool:
        """Return whether a target id is explicitly in scope."""
        return target_id in self.target_ids

    def allows_tool(self, tool_name: str) -> bool:
        """Return whether a tool is allowed, with deny rules winning."""
        if tool_name in self.denied_tools:
            return False
        return tool_name in self.allowed_tools

    def allows_domain(self, domain: str) -> bool:
        """Return whether network access to a domain is allowed."""
        if not self.can_use_network:
            return False
        if self._matches_any_domain(domain, self.denied_domains):
            return False
        return self._matches_any_domain(domain, self.allowed_domains)

    @staticmethod
    def _matches_any_domain(domain: str, candidates: list[str]) -> bool:
        clean_domain = domain.lower().strip().removeprefix("https://").removeprefix("http://")
        clean_domain = clean_domain.split("/", 1)[0].split(":", 1)[0]
        for candidate in candidates:
            clean_candidate = candidate.lower().strip()
            if clean_domain == clean_candidate or clean_domain.endswith(f".{clean_candidate}"):
                return True
        return False
