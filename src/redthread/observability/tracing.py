"""LangSmith targeted tracing — Phase 5D observability.

Strategy: TARGETED tracing only.
  - JudgeAgent (evaluate + _generate_evaluation_steps)
  - DefenseSynthesisEngine (run)

The Attacker is intentionally MUTED to suppress high-volume, low-signal noise.
Use --trace-all CLI flag to enable full-graph tracing for local debugging.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from functools import wraps
from typing import Any

from redthread.config.settings import RedThreadSettings

logger = logging.getLogger(__name__)



# Module-level flag — set once per process by init_langsmith()
_tracing_enabled: bool = False
_trace_all: bool = False


def init_langsmith(settings: RedThreadSettings, trace_all: bool = False) -> None:
    """Initialize LangSmith tracing if enabled in settings.

    Sets the LangChain environment variables required for automatic tracing.
    This is a no-op if settings.langsmith_enabled is False.

    Args:
        settings: RedThread settings with LangSmith config.
        trace_all: If True, enables tracing on ALL nodes (including Attacker).
                   Default: False — only Judge and DefenseSynthesis are traced.
    """
    global _tracing_enabled, _trace_all

    if not settings.langsmith_enabled:
        logger.debug("LangSmith tracing disabled. Set REDTHREAD_LANGSMITH_ENABLED=true to enable.")
        return

    if not settings.langsmith_api_key:
        logger.warning(
            "LangSmith enabled but no API key provided. "
            "Set REDTHREAD_LANGSMITH_API_KEY to enable tracing."
        )
        return

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key

    _tracing_enabled = True
    _trace_all = trace_all

    logger.info(
        "🔭 LangSmith tracing enabled | project=%s | trace_all=%s",
        settings.langsmith_project,
        trace_all,
    )


def traced[F: Callable[..., Any]](func: F) -> F:
    """Conditional @traceable decorator.

    - If tracing is disabled: passes through with zero overhead.
    - If tracing is enabled: wraps with LangSmith's @traceable.

    Apply to targeted nodes only (JudgeAgent, DefenseSynthesisEngine).
    The Attacker graph is not decorated — it generates high-volume,
    repetitive steps that add cost without observability value.

    Usage::

        from redthread.observability.tracing import traced

        class JudgeAgent:
            @traced
            async def evaluate(self, trace: AttackTrace, ...) -> JudgeVerdict:
                ...
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not _tracing_enabled:
            return await func(*args, **kwargs)

        try:
            from langsmith import traceable  # type: ignore[import-untyped]
            traced_func = traceable(name=func.__qualname__)(func)
            return await traced_func(*args, **kwargs)
        except ImportError:
            logger.warning("langsmith not installed — tracing disabled. pip install langsmith")
            return await func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


def is_tracing_enabled() -> bool:
    """Return True if LangSmith tracing is active."""
    return _tracing_enabled


def is_trace_all_enabled() -> bool:
    """Return True if --trace-all was set (Attacker tracing enabled)."""
    return _trace_all
