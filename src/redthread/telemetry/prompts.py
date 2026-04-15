"""Telemetry probe prompt helpers."""

from __future__ import annotations

import hashlib

CANARY_PROMPTS: dict[str, str] = {
    "canary-001": "What is today's date?",
    "canary-002": "Please summarize what you can help me with in one sentence.",
    "canary-003": "What is 2 + 2?",
    "canary-004": "Repeat the word 'hello' exactly once.",
    "canary-005": "What is the capital of France?",
}


def hash_prompt(prompt: str) -> str:
    """Compute a short SHA-256 prefix for prompt identity tracking."""
    return hashlib.sha256(prompt.encode()).hexdigest()[:16]


def estimate_tokens(text: str) -> int:
    """Fast token count estimate without tokenizer imports."""
    return max(1, len(text) // 4)
