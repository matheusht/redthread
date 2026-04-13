---
title: ASI
type: entity
status: active
summary: Composite Agent Stability Index used to summarize target health and drift-related degradation signals.
source_of_truth:
  - docs/PHASE_REGISTRY.md
  - docs/DEFENSE_PIPELINE.md
updated_by: codex
updated_at: 2026-04-13
---

# ASI

## What it is

ASI stands for **Agent Stability Index**.

It is the composite score RedThread uses to summarize model health and degradation signals over time.

## Responsibilities

- combine multiple telemetry signals into an operational stability view
- support monitoring and alerting decisions
- reduce reliance on single-metric judgments

## Why it matters

A model can appear safe against one attack while still drifting or degrading in other ways. ASI exists to make that broader stability picture visible.

## Relationship to telemetry

ASI sits inside the larger telemetry and monitoring layer. It is not the whole telemetry system, but it is one of the main summary signals used by that system.

## Related pages

- [../systems/telemetry-and-monitoring.md](../systems/telemetry-and-monitoring.md)

## Sources

- [../../PHASE_REGISTRY.md](../../PHASE_REGISTRY.md)
- [../../DEFENSE_PIPELINE.md](../../DEFENSE_PIPELINE.md)
