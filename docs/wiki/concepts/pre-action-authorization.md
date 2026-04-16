---
title: Pre-Action Authorization
type: concept
status: active
summary: Deterministic, policy-based enforcement before LLM tool call execution.
source_of_truth:
  - https://arxiv.org/abs/2603.20953
updated_by: codex
updated_at: 2026-04-16
---

# Pre-Action Authorization

## Definition

Intercepting a tool call *before* it happens. Comparing it to a hard policy. Blocking if it fails.

## Why it matters

Current safety is "probabilistic". Models skip rules by mistake.
Pre-Action Authorization is "deterministic". It is a hard gate.
It stops social engineering from reaching sensitive tools.

## Deterministic vs Probabilistic

| Mode | Type | Reliability |
| :--- | :--- | :--- |
| **Model Alignment** | Probabilistic | Low (can be bypassed) |
| **Evaluation** | Probabilistic | Medium (post-hoc) |
| **OAP / Authorization** | Deterministic | High (hard gate) |

## Sources

- [Arxiv 2603.20953: Before the Tool Call](https://arxiv.org/abs/2603.20953)
