"""Shared fixtures for JudgeAgent tests."""

from __future__ import annotations

from redthread.config.settings import RedThreadSettings, TargetBackend


def make_settings() -> RedThreadSettings:
    return RedThreadSettings(
        judge_backend=TargetBackend.OPENAI,
        judge_model="gpt-4o",
        openai_api_key="test-key",
        attacker_backend=TargetBackend.OLLAMA,
        attacker_model="llama3.2:3b",
        target_backend=TargetBackend.OLLAMA,
        target_model="llama3.2:3b",
    )
