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
from redthread.pyrit_adapters.send_helpers import send_with_execution_metadata

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
    "send_with_execution_metadata",
    "_build_pyrit_target",
]
