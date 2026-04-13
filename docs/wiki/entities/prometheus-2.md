---
title: Prometheus 2
type: entity
status: active
summary: Evaluation model referenced as a key scoring component in RedThread's grounded judging stack.
source_of_truth:
  - docs/product.md
  - docs/ANTI_HALLUCINATION_SOP.md
updated_by: codex
updated_at: 2026-04-13
---

# Prometheus 2

## What it is

Prometheus 2 is the evaluation model referenced by RedThread as part of its judging and scoring stack.

## Responsibilities

- support direct assessment style evaluation
- contribute to grounded scoring behavior
- reinforce the separation between creative attack generation and reliable evaluation

## Why it matters

RedThread's evaluation layer depends on models that are better suited to scoring than general-purpose, high-creativity generation.

## Related pages

- [judge-agent.md](judge-agent.md)
- [../systems/evaluation-and-anti-hallucination.md](../systems/evaluation-and-anti-hallucination.md)

## Sources

- [../../product.md](../../product.md)
- [../../ANTI_HALLUCINATION_SOP.md](../../ANTI_HALLUCINATION_SOP.md)
