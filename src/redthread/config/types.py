"""Shared configuration enum types."""

from __future__ import annotations

from enum import Enum


class AlgorithmType(str, Enum):
    AGENT_CHAIN = "agent_chain"
    PAIR = "pair"
    TAP = "tap"
    CRESCENDO = "crescendo"
    MCTS = "mcts"


class TargetBackend(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    LLAMA_CPP = "llama_cpp"


class CanaryPolicyPreset(str, Enum):
    MONITOR_ONLY = "monitor_only"
    BLOCK_EXECUTION_BOUNDARY = "block_execution_boundary"
    BLOCK_MEMORY_AND_OUTBOUND = "block_memory_and_outbound"
    STRICT_FAIL_CLOSED = "strict_fail_closed"


class ModelRole(str, Enum):
    """Asymmetric deployment roles."""

    ATTACKER = "attacker"
    JUDGE = "judge"
    TARGET = "target"
    DEFENSE_ARCHITECT = "defense"


class SettingsProfile(str, Enum):
    """Small operator profile surface."""

    DEFAULT = "default"
    RESEARCH = "research"
    CI = "ci"


__all__ = [
    "AlgorithmType",
    "CanaryPolicyPreset",
    "ModelRole",
    "SettingsProfile",
    "TargetBackend",
]
