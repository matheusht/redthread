---
title: Defense Architect
type: entity
status: active
summary: The grounded generation role that proposes exploit-scoped guardrails during defense synthesis.
source_of_truth:
  - docs/ANTI_HALLUCINATION_SOP.md
  - docs/DEFENSE_PIPELINE.md
  - docs/PHASE_REGISTRY.md
updated_by: codex
updated_at: 2026-04-13
---

# Defense Architect

## What it is

The Defense Architect is the role that generates candidate defensive clauses after a jailbreak has been confirmed.

## Responsibilities

- classify the exploit pattern
- generate a candidate guardrail proposal
- stay grounded and exploit-scoped rather than broad or overly-refusal-oriented
- participate in the validated defense pipeline rather than directly mutating production state

## Why it matters

RedThread explicitly treats defense generation as a grounded, high-stakes path.

This is why the project docs emphasize model separation and low-temperature behavior for defensive generation.

## Relationship to validation

A proposed clause is not automatically deployable.

The Defense Architect's output must pass validation and promotion discipline before it is treated as production-worthy.

## Related pages

- [../systems/promotion-and-revalidation.md](../systems/promotion-and-revalidation.md)
- [../systems/evaluation-and-anti-hallucination.md](../systems/evaluation-and-anti-hallucination.md)

## Sources

- [../../ANTI_HALLUCINATION_SOP.md](../../ANTI_HALLUCINATION_SOP.md)
- [../../DEFENSE_PIPELINE.md](../../DEFENSE_PIPELINE.md)
- [../../PHASE_REGISTRY.md](../../PHASE_REGISTRY.md)
