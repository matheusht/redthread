---
title: LangGraph Supervisor
type: entity
status: active
summary: Coordinator role that manages RedThread's macro-workflow and routes work across attack, judge, and defense phases.
source_of_truth:
  - docs/TECH_STACK.md
  - docs/AGENT_ARCHITECTURE.md
  - docs/PHASE_REGISTRY.md
updated_by: codex
updated_at: 2026-04-13
---

# LangGraph Supervisor

## What it is

The LangGraph Supervisor is RedThread's coordinator-style orchestration role.

## Responsibilities

- manage macro-workflow state
- route execution between attack, evaluation, and defense paths
- coordinate fan-out and fan-in style multi-agent behavior
- keep phase ordering explicit and inspectable

## Why it matters

It is the main bridge between isolated worker behavior and the broader campaign lifecycle.

## Related pages

- [../systems/knowledge-stack.md](../systems/knowledge-stack.md)
- [../systems/promotion-and-revalidation.md](../systems/promotion-and-revalidation.md)

## Sources

- [../../TECH_STACK.md](../../TECH_STACK.md)
- [../../AGENT_ARCHITECTURE.md](../../AGENT_ARCHITECTURE.md)
- [../../PHASE_REGISTRY.md](../../PHASE_REGISTRY.md)
