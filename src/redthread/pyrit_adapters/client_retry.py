"""Exponential backoff and retry helper for PyRIT target adapters."""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_RETRYABLE_PHRASES = (
    "429",
    "503",
    "rate limit",
    "ratelimit",
    "too many requests",
    "overloaded",
    "temporarily unavailable",
    "connection reset",
    "connection error",
    "timeout",
)


def is_retryable_error(exc: Exception) -> bool:
    """Return True if exception represents a transient/rate-limit error."""
    status = getattr(exc, "status", None) or getattr(exc, "status_code", None)
    if status in _RETRYABLE_STATUS_CODES:
        return True
    if isinstance(exc, (ConnectionError, TimeoutError, asyncio.TimeoutError)):
        return True
    msg = str(exc).lower()
    return any(phrase in msg for phrase in _RETRYABLE_PHRASES)


async def send_with_retry(
    call: Callable[[], Coroutine[Any, Any, T]],
    *,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    backoff_factor: float = 2.0,
    max_delay: float = 5.0,
) -> T:
    """Execute async call with exponential backoff and jitter on retryable errors."""
    delay = initial_delay
    for attempt in range(max_retries + 1):
        try:
            return await call()
        except Exception as exc:
            if attempt < max_retries and is_retryable_error(exc):
                jitter = random.uniform(0.01, 0.05)
                sleep_time = min(delay + jitter, max_delay)
                logger.warning(
                    "Retryable error on attempt %d/%d: %s. Retrying in %.2fs",
                    attempt + 1,
                    max_retries,
                    exc,
                    sleep_time,
                )
                await asyncio.sleep(sleep_time)
                delay *= backoff_factor
                continue
            raise
    # ponytail: unreachable fallback
    return await call()
