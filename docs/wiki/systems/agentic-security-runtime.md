---
title: Agentic Security Runtime
type: system
status: active
summary: How Phase 8 agentic-security components now plug into RedThread's normal campaign runtime as an additive sealed review lane.
source_of_truth:
  - docs/AGENTIC_SECURITY_RUNTIME.md
  - docs/AGENTIC_SECURITY_THREAT_MODEL.md
  - docs/PHASE_REGISTRY.md
  - src/redthread/orchestration/agentic_security_runtime.py
  - src/redthread/orchestration/supervisor.py
  - src/redthread/orchestration/runtime_summary.py
  - src/redthread/engine.py
  - tests/test_supervisor.py
  - tests/test_runtime_truth.py
updated_by: codex
updated_at: 2026-04-17
---

# Agentic Security Runtime

## Scope

This page explains the new Phase 8 runtime hook that adds agentic-security review to the normal RedThread campaign path.

This is not a replacement runtime.
It is an additive review lane.

## Runtime position

Current supervisor flow now is:
1. generate personas
2. run attack workers
3. collect results
4. judge results
5. run additive agentic-security review
6. route to defense if jailbreaks exist
7. finalize campaign

This matters because Phase 8 is no longer only sidecar code and tests.
It now shows up in normal campaign artifacts.

## What gets reviewed

The runtime hook wakes up when the campaign objective or target prompt suggests:
- tools or MCP/function-calling surfaces
- multi-agent delegation or supervisor/worker flows
- retry, repair, fallback, token, or budget-loop risk

The current review runs sealed deterministic checks for:
- tool poisoning
- confused deputy / privilege laundering
- resource amplification

## What controls are exercised

The runtime review uses the shipped Phase 8 control pieces:
- `ActionEnvelope`
- provenance and lineage metadata
- deterministic authorization engine
- shared capability taxonomy
- permission inheritance logic
- canary propagation report
- runtime budget evaluator

## Trust-core hardening status

Current trust-core hardening now includes:
- shared capability classification for read-only, write, execution, delegation, exfiltration, config mutation, memory mutation, network egress, and secret access
- permission inheritance and trusted fallback behavior both using the same capability taxonomy
- enum-backed `required_trust_levels` instead of raw string checks
- canonical trust meaning centered on `trust_level`, with `derived_from_untrusted` normalized from it for compatibility
- explicit authorization precedence: permission inheritance, deny policies, escalate policies, allow policies, then safe fallback

This matters because the biggest Phase 8 risk was not missing more synthetic threats first.
It was weak trust semantics in the core decision path.

This means a normal campaign can now expose whether the current deterministic controls would:
- allow
- deny
- escalate
- contain canaries before execution
- stop amplification loops

## Where the evidence appears

The campaign now records:
- `metadata.agentic_security_report`
- `metadata.runtime_summary.agentic_security`
- transcript summary line `agentic_security_report`

The compact runtime summary currently surfaces:
- action totals
- authorization decision counts
- canary event totals
- canary report
- amplification metrics
- budget stop state
- untrusted-lineage action totals

## Evidence honesty

Current runtime review evidence is `sealed_runtime_review`.

That is useful for:
- operator visibility
- deterministic control validation
- replay and promotion preparation

That is not the same as:
- live policy interception proof
- live tool-execution containment proof
- universal production safety proof

## Live-proof lane

A tiny opt-in live-proof lane now exists through `run_live_authorization_smoke()`.
It is a controlled local interception hook that proves one real pre-action boundary:
- deny or escalate means the callback does not run
- allow means the callback runs

That same pattern now also reaches `ControlledLiveAdapter` and `AttackTool`.
When `ControlledLiveAdapter.send(..., action=...)` receives an `ActionEnvelope`, it can block the wrapped live target call before execution.
When `AttackTool` receives an `ActionEnvelope` in tool context metadata, it can block the live target send before execution.

This is useful because it proves the deterministic authorization decision can sit on the execution boundary itself.

It still does not prove broad production enforcement.
The next gap is connecting the same pattern to richer adapters without overstating coverage.

## Why this is a good fit for RedThread

RedThread already separates:
- creative attack generation
- grounded judging
- validation and promotion

The new runtime hook keeps that style.
It adds deterministic agentic checks without replacing the old jailbreak lane.

## Bottom line

Phase 8 now touches the real campaign runtime.

RedThread can now do normal attack campaigns and also attach a sealed agentic-security review when the target looks like a tool-using or multi-agent system.
