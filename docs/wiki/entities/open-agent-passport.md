---
title: Open Agent Passport (OAP)
type: entity
status: active
summary: Open specification for deterministic tool call authorization.
source_of_truth:
  - https://arxiv.org/abs/2603.20953
updated_by: codex
updated_at: 2026-04-16
---

# Open Agent Passport (OAP)

## What it is

An open specification for synchronous tool call interception. 
It creates a cryptographically signed audit record for every action.

## Responsibilities

- **Intercept:** Stop tool call before execution.
- **Evaluate:** Check against a declarative policy (e.g. "max $50 spend").
- **Audit:** Sign the decision and record the evidence.

## Performance

- **Median Latency:** 53 ms.
- **Success Rate:** Stopped 100% of attacks in live testbed under restrictive policy.

## Sources

- [Arxiv 2603.20953: Before the Tool Call](https://arxiv.org/abs/2603.20953)
