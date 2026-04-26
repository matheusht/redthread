"""Risk plugin contracts for campaign planning."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class RiskCategory(str, Enum):
    """High-level risk areas RedThread can test."""

    PROMPT_INJECTION = "prompt_injection"
    SYSTEM_PROMPT_LEAKAGE = "system_prompt_leakage"
    SENSITIVE_DATA_EXFILTRATION = "sensitive_data_exfiltration"
    UNSAFE_TOOL_USE = "unsafe_tool_use"
    CROSS_SESSION_DATA_LEAK = "cross_session_data_leak"
    UNAUTHORIZED_ACTION = "unauthorized_action"
    CUSTOM_POLICY = "custom_policy"


class TargetType(str, Enum):
    """Target surfaces a risk plugin can apply to."""

    LLM = "llm"
    CHAT_AGENT = "chat_agent"
    RAG = "rag"
    TOOL_AGENT = "tool_agent"
    WORKFLOW_AGENT = "workflow_agent"
    API = "api"


class RiskPlugin(BaseModel):
    """RedThread-native description of what risk or policy to test."""

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$", min_length=1)
    name: str = Field(min_length=1)
    category: RiskCategory
    description: str = ""
    policy_text: str = ""
    examples: list[str] = Field(default_factory=list)
    expected_failure_modes: list[str] = Field(default_factory=list)
    applicable_target_types: list[TargetType] = Field(
        default_factory=lambda: [TargetType.CHAT_AGENT]
    )
    default_strategy_ids: list[str] = Field(default_factory=list)
    judge_rubric_id: str = "authorization_bypass"
    owasp_tags: list[str] = Field(default_factory=list)
    mitre_tags: list[str] = Field(default_factory=list)
    nist_tags: list[str] = Field(default_factory=list)
    source: str = "redthread_builtin"

    def applies_to(self, target_type: TargetType) -> bool:
        """Return whether this plugin applies to a target type."""
        return target_type in self.applicable_target_types

    def has_framework_tag(self, tag: str) -> bool:
        """Return whether any framework tag matches exactly."""
        return tag in {*self.owasp_tags, *self.mitre_tags, *self.nist_tags}
