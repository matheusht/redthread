"""Task state machine — modeled after Claude Code's Task.ts.

Every background operation in RedThread is a typed task with:
  - Deterministic, type-prefixed ID generation
  - Validated state transitions (pending → running → completed|failed|killed)
  - Timing metadata (start_time, end_time, total_paused_ms)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED = "killed"


class TaskType(str, Enum):
    CAMPAIGN = "campaign"           # Top-level red-team run
    ATTACK_RUN = "attack_run"       # Single attacker vs. target session
    JUDGE_EVAL = "judge_eval"       # Evaluation of a single trace
    DEFENSE_SYNTH = "defense_synth" # Guardrail generation (Phase 5)
    SANDBOX_TEST = "sandbox_test"   # Regression validation (Phase 5)
    DREAM = "dream"                 # Memory consolidation


# Valid state transitions — mirrors Claude Code's lifecycle logic
_VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PENDING: {TaskStatus.RUNNING, TaskStatus.KILLED},
    TaskStatus.RUNNING: {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.KILLED},
    TaskStatus.COMPLETED: set(),    # Terminal
    TaskStatus.FAILED: set(),       # Terminal
    TaskStatus.KILLED: set(),       # Terminal
}


def generate_task_id(task_type: TaskType) -> str:
    """Deterministic, type-prefixed ID — e.g., 'attack_run-3f2a1b'."""
    short_uuid = str(uuid4()).replace("-", "")[:6]
    return f"{task_type.value}-{short_uuid}"


@dataclass
class Task:
    """A unit of tracked work in the RedThread engine."""

    id: str
    type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    result: Any | None = None
    error: str | None = None

    # Timing — all in seconds since epoch (monotonic for durations)
    _start_time: float | None = field(default=None, repr=False)
    _end_time: float | None = field(default=None, repr=False)
    _total_paused_ms: int = field(default=0, repr=False)

    @classmethod
    def create(cls, task_type: TaskType) -> "Task":
        return cls(id=generate_task_id(task_type), type=task_type)

    def transition(self, new_status: TaskStatus) -> None:
        """Validated state transition — raises ValueError on illegal moves."""
        allowed = _VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Invalid transition: {self.status} → {new_status} "
                f"(task {self.id}). Allowed: {allowed}"
            )
        self.status = new_status

        if new_status == TaskStatus.RUNNING:
            self._start_time = time.monotonic()
        elif new_status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.KILLED):
            self._end_time = time.monotonic()

    def start(self) -> None:
        self.transition(TaskStatus.RUNNING)

    def complete(self, result: Any = None) -> None:
        self.result = result
        self.transition(TaskStatus.COMPLETED)

    def fail(self, error: str) -> None:
        self.error = error
        self.transition(TaskStatus.FAILED)

    def kill(self) -> None:
        self.transition(TaskStatus.KILLED)

    @property
    def duration_seconds(self) -> float | None:
        if self._start_time is None:
            return None
        end = self._end_time or time.monotonic()
        return end - self._start_time

    @property
    def is_terminal(self) -> bool:
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.KILLED)
