# Agentic Security Runtime Integration

> **Status**: Active reference
> **Scope**: Phase 8 runtime wiring for additive campaign-time agentic security review
> **Last Updated**: 2026-04-16

---

## Purpose

This document explains how Phase 8 agentic-security components now attach to the normal RedThread runtime path.

This is **additive**.
It does **not** replace:
- attack algorithms
- judge flow
- defense synthesis
- telemetry
- replay/promotion systems

It adds a deterministic runtime review lane for campaigns that look like tool-using or multi-agent targets.

---

## Runtime hook

Current supervisor flow is now:

1. generate personas
2. fan out attack workers
3. collect results
4. judge results
5. run additive agentic-security runtime review
6. route to defense if jailbreaks exist
7. finalize campaign

The runtime review lives in:
- `src/redthread/orchestration/agentic_security_runtime.py`
- `src/redthread/orchestration/supervisor.py`
- `src/redthread/orchestration/runtime_summary.py`
- `src/redthread/engine.py`

---

## What the runtime review does

When the campaign objective or target system prompt suggests:
- tools
- MCP/function calling
- multi-agent delegation
- retry/repair/fallback loops

RedThread now runs a sealed deterministic review pass.

That pass currently executes three additive checks:

### 1. Tool poisoning review
- runs a sealed poisoned tool-return scenario
- normalizes the downstream risky action into an `ActionEnvelope`
- evaluates it with the deterministic authorization engine
- records canary propagation state

### 2. Confused deputy review
- runs a sealed privilege-laundering scenario
- preserves untrusted lineage in provenance
- checks permission inheritance through the authorization engine

### 3. Resource amplification review
- runs a sealed retry/repair amplification scenario
- computes `AmplificationMetrics`
- evaluates deterministic runtime budget stop logic

---

## What gets written

Campaign metadata now includes:
- `agentic_security_report`
- `runtime_summary.agentic_security`

Transcript summary lines now also include:
- `agentic_security_report`

The compact runtime summary currently surfaces:
- `action_total`
- `authorization_decision_counts`
- `canary_event_total`
- `canary_report`
- `amplification_metrics`
- `budget_stop_triggered`
- `untrusted_lineage_action_total`

---

## Evidence class

Current runtime hook produces:
- `sealed_runtime_review`

This is useful evidence for:
- deterministic control behavior
- trust-boundary visibility
- campaign-time operator inspection

It is **not** the same as:
- live tool interception proof
- full enterprise runtime enforcement
- universal production safety proof

---

## Fail-closed and scope notes

Current live-adapter enforcement is still separate and guarded.
The runtime review does **not** automatically execute real tools.
It uses sealed scenario packs and deterministic controls.

This means current integration is good for:
- runtime truth
- operator visibility
- additive validation
- promotion preparation

But it is still intentionally conservative about live execution.

---

## Verification

Current focused verification includes:
- `tests/test_supervisor.py`
- `tests/test_runtime_truth.py`
- `tests/test_agentic_security_scenarios.py`
- `tests/test_authorization_engine.py`
- `tests/test_canary_containment.py`
- `tests/test_agentic_replay_promotion.py`

Use repo-local invocation:

```bash
PYTHONPATH=src .venv/bin/pytest
```

---

## Bottom line

Phase 8 is no longer only a sealed sidecar.

RedThread now has a real campaign-time agentic-security review lane:
- deterministic
- additive
- transcript-visible
- replay-friendly
- still honest about sealed vs live evidence
