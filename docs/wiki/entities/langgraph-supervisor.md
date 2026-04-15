---
title: LangGraph Supervisor
type: entity
status: active
summary: Coordinator role that manages RedThread's macro-workflow and routes work across attack, judge, and defense phases.
source_of_truth:
  - docs/TECH_STACK.md
  - docs/AGENT_ARCHITECTURE.md
  - docs/PHASE_REGISTRY.md
  - src/redthread/orchestration/supervisor.py
  - src/redthread/orchestration/graphs/judge_graph.py
updated_by: codex
updated_at: 2026-04-15
---

# LangGraph Supervisor

## What it is

The LangGraph Supervisor is RedThread's coordinator-style orchestration role.

## Responsibilities

- manage macro-workflow state
- route execution between attack, evaluation, and defense paths
- coordinate fan-out and fan-in style multi-agent behavior
- keep phase ordering explicit and inspectable
- surface degraded-runtime truth when worker errors happen

## Runtime truth notes

Current runtime shape is:
- attack workers fan out in parallel
- judge and defense phases still execute as sequential loops
- campaign artifacts now include degraded-runtime summary fields
- per-trace judge passthrough is explicitly labeled instead of being silent

## Why it matters

It is the main bridge between isolated worker behavior and the broader campaign lifecycle.

## Related pages

- [../systems/knowledge-stack.md](../systems/knowledge-stack.md)
- [../systems/promotion-and-revalidation.md](../systems/promotion-and-revalidation.md)

## Sources

- [../../TECH_STACK.md](../../TECH_STACK.md)
- [../../AGENT_ARCHITECTURE.md](../../AGENT_ARCHITECTURE.md)
- [../../PHASE_REGISTRY.md](../../PHASE_REGISTRY.md)
