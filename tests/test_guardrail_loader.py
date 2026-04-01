"""Tests for the GuardrailLoader — Phase 4.5.

Verifies:
  - Scoped guardrails from MEMORY.md are injected correctly
  - Non-matching scopes are ignored
  - Missing memory files are handled gracefully
"""

from __future__ import annotations

import hashlib

import pytest

from redthread.config.settings import RedThreadSettings, TargetBackend
from redthread.core.defense_synthesis import (
    DeploymentRecord,
    GuardrailProposal,
    IsolatedSegment,
    ValidationResult,
    VulnerabilityClassification,
)
from redthread.core.guardrail_loader import GuardrailLoader
from redthread.memory.index import MemoryIndex
from redthread.models import CampaignConfig


def make_settings(tmp_path) -> RedThreadSettings:
    return RedThreadSettings(
        target_backend=TargetBackend.OLLAMA,
        target_model="llama3.2:3b",
        attacker_backend=TargetBackend.OLLAMA,
        attacker_model="llama3.2:3b",
        judge_backend=TargetBackend.OPENAI,
        judge_model="gpt-4o",
        openai_api_key="test-key",
        dry_run=True,
    ).model_copy(update={"memory_dir": tmp_path})


def make_deployment_record(
    trace_id: str,
    clause: str,
    target_model: str,
    prompt_hash: str,
    passed: bool = True,
) -> DeploymentRecord:
    cl = VulnerabilityClassification(
        category="test_cat",
        owasp_ref="LLM01",
        mitre_atlas_ref="AML.T0000",
        severity="HIGH",
        attack_vector="Test vector",
    )
    val = ValidationResult(passed=passed, replay_response="Mock", judge_score=1.0)
    return DeploymentRecord(
        trace_id=trace_id,
        guardrail_clause=clause,
        classification=cl,
        validation=val,
        target_model=target_model,
        target_system_prompt_hash=prompt_hash,
    )


def test_guardrail_loader_injects_scoped_clauses(tmp_path) -> None:
    settings = make_settings(tmp_path)
    base_prompt = "You are a helpful assistant."
    prompt_hash = hashlib.sha256(base_prompt.encode("utf-8")).hexdigest()[:16]

    index = MemoryIndex(settings)
    
    # 1. Matching scope, passed validation
    r1 = make_deployment_record("trace-1", "Do not leak PII.", "llama3.2:3b", prompt_hash)
    index.append(r1)

    # 2. Matching scope, FAILED validation (should not be loaded)
    r2 = make_deployment_record("trace-2", "Do not help.", "llama3.2:3b", prompt_hash, passed=False)
    index.append(r2)

    # 3. Different model scope
    r3 = make_deployment_record("trace-3", "Different model.", "gpt-4o", prompt_hash)
    index.append(r3)

    # 4. Different prompt hash
    r4 = make_deployment_record("trace-4", "Different prompt.", "llama3.2:3b", "abcdef123")
    index.append(r4)

    loader = GuardrailLoader(settings, index)
    
    config = CampaignConfig(
        objective="Test",
        target_system_prompt=base_prompt,
        num_personas=1,
        rubric_name="default",
    )

    injected = loader.inject_guardrails(config)

    # Only "Do not leak PII." should be included
    assert "## ACTIVE SECURITY GUARDRAILS" in injected.target_system_prompt
    assert "1. Do not leak PII." in injected.target_system_prompt
    assert "Do not help." not in injected.target_system_prompt
    assert "Different model." not in injected.target_system_prompt
    assert "Different prompt." not in injected.target_system_prompt


def test_guardrail_loader_skips_when_no_guardrails_active(tmp_path) -> None:
    settings = make_settings(tmp_path)
    base_prompt = "You are a helpful assistant."
    
    # Empty index
    index = MemoryIndex(settings)
    loader = GuardrailLoader(settings, index)
    
    config = CampaignConfig(
        objective="Test",
        target_system_prompt=base_prompt,
        num_personas=1,
        rubric_name="default",
    )

    injected = loader.inject_guardrails(config)

    # Should be perfectly identical
    assert injected.target_system_prompt == base_prompt
