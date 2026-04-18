from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token

from redthread.pyrit_adapters.execution_records import ExecutionMetadata


class LiveExecutionInterceptionError(RuntimeError):
    """Raised when a common-boundary live send is blocked before execution."""


ExecutionInterceptor = Callable[[ExecutionMetadata], None]
_CURRENT_INTERCEPTOR: ContextVar[ExecutionInterceptor | None] = ContextVar(
    "redthread_execution_interceptor",
    default=None,
)


@contextmanager
def intercept_live_execution(interceptor: ExecutionInterceptor) -> Iterator[None]:
    token: Token[ExecutionInterceptor | None] = _CURRENT_INTERCEPTOR.set(interceptor)
    try:
        yield
    finally:
        _CURRENT_INTERCEPTOR.reset(token)


def maybe_intercept_live_execution(execution_metadata: ExecutionMetadata | None) -> None:
    interceptor = _CURRENT_INTERCEPTOR.get()
    if interceptor is None or execution_metadata is None:
        return
    interceptor(execution_metadata)
