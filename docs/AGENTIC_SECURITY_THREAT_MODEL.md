# Agentic Security Threat Model

> **Status**: Active reference
> **Scope**: Phase 8A schema and threat vocabulary
> **Last Updated**: 2026-04-16

---

## Purpose

This document defines the additive threat vocabulary for RedThread's Phase 8 agentic-security expansion.

It does **not** replace the existing jailbreak-focused threat model.
It extends RedThread so the project can reason about execution-time risk in tool-using and multi-agent systems.

---

## Core shift

Old focus:
- unsafe text
- prompt refusal bypass
- single-agent jailbreak outcomes

New focus:
- unsafe actions
- tool misuse
- trust-boundary contamination
- delegated privilege abuse
- token and cost amplification
- deterministic containment before execution

---

## Threat families

### 1. Tool poisoning
Untrusted tool metadata or tool returns steer the agent toward unsafe follow-up actions.

### 2. Tool leak
A tool schema or argument description induces the model to place hidden instructions or sensitive context into a routine tool argument.

### 3. Cross-tool contamination
One tool poisons shared context, causing a later unrelated tool to be used unsafely.

### 4. Confused deputy
A low-trust or low-privilege component manipulates a high-trust component into taking an action on its behalf.

### 5. Privilege laundering
Authority is gained indirectly through lineage loss, shared state, or delegation without permission inheritance.

### 6. Resource amplification
An agent is pushed into retry loops, reflection loops, fallback storms, or other expensive behavior that multiplies cost and latency.

### 7. Canary propagation
Markers are used to detect whether untrusted content crossed summarization, planning, or execution boundaries.

### 8. Deterministic containment
A non-LLM control plane blocks or escalates risky actions before execution.

---

## First-class concepts

### Provenance
Every risky request should carry origin and trust metadata.

### Action envelope
Every sensitive action should be normalized into one common schema for evaluation and control.

### Boundary crossing
Important trust boundaries include:
- tool return
- agent handoff
- shared state
- execution plan
- memory write
- outbound request

### Amplification metrics
Phase 8 should measure:
- tool call count
- retries
- duplicate calls
- loop depth
- fallback count
- token growth ratio
- budget breach state

---

## Phase 8A promise

Phase 8A only adds the schema and shared vocabulary.
It does not yet add:
- live tool interception
- deterministic policy enforcement
- canary runtime hooks
- live MCP integrations

Those come in later Phase 8 steps.
