from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token

from redthread.pyrit_adapters.execution_records import ExecutionRecord, ExecutionRecorder

_CURRENT_EXECUTION_RECORDER: ContextVar[ExecutionRecorder | None] = ContextVar(
    "redthread_execution_recorder",
    default=None,
)


def get_execution_recorder() -> ExecutionRecorder | None:
    return _CURRENT_EXECUTION_RECORDER.get()


@contextmanager
def capture_execution_records(records: list[ExecutionRecord]) -> Iterator[None]:
    token: Token[ExecutionRecorder | None] = _CURRENT_EXECUTION_RECORDER.set(records.append)
    try:
        yield
    finally:
        _CURRENT_EXECUTION_RECORDER.reset(token)
