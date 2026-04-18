"""Compatibility exports for the shared PyRIT adapter boundary."""

from redthread.pyrit_adapters.client import RedThreadTarget
from redthread.pyrit_adapters.execution_records import (
    ExecutionMetadata,
    ExecutionRecord,
    ExecutionRecorder,
    build_execution_record,
)
from redthread.pyrit_adapters.factories import (
    build_attacker,
    build_defense_architect,
    build_judge_llm,
    build_rollout_attacker,
    build_target,
)
from redthread.pyrit_adapters.runtime import _build_pyrit_target, ensure_pyrit_memory_initialized

__all__ = [
    "ExecutionMetadata",
    "ExecutionRecord",
    "ExecutionRecorder",
    "RedThreadTarget",
    "build_attacker",
    "build_defense_architect",
    "build_execution_record",
    "build_judge_llm",
    "build_rollout_attacker",
    "build_target",
    "ensure_pyrit_memory_initialized",
    "_build_pyrit_target",
]
