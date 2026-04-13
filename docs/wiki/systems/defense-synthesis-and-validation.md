---
title: Defense Synthesis and Validation
type: system
status: active
summary: How RedThread turns confirmed jailbreaks into validated defensive proposals rather than raw findings alone.
source_of_truth:
  - docs/DEFENSE_PIPELINE.md
  - docs/PHASE_REGISTRY.md
updated_by: codex
updated_at: 2026-04-13
---

# Defense Synthesis and Validation

## Scope

This page summarizes the self-healing path from confirmed jailbreak to validated defensive evidence.

## Workflow

The documented pipeline follows a clear pattern:
1. isolate the relevant exploit slice
2. classify the attack pattern
3. generate a defensive proposal
4. validate it through replay / sealed checks
5. preserve evidence for later promotion decisions

## Why it matters

This is the core difference between a tool that only reports failures and one that helps close the loop on remediation.

## Guardrails

- proposals are not treated as production-ready by default
- validation evidence matters as much as the proposal text
- promotion stays separate from generation

## Related pages

- [promotion-and-revalidation.md](promotion-and-revalidation.md)
- [evaluation-and-anti-hallucination.md](evaluation-and-anti-hallucination.md)
- [../entities/defense-architect.md](../entities/defense-architect.md)

## Sources

- [../../DEFENSE_PIPELINE.md](../../DEFENSE_PIPELINE.md)
- [../../PHASE_REGISTRY.md](../../PHASE_REGISTRY.md)
