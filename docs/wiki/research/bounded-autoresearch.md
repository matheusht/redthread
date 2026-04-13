---
title: Bounded Autoresearch
type: research
status: active
summary: Current synthesis of RedThread's bounded offense and defense mutation lanes and their safety constraints.
source_of_truth:
  - docs/AUTORESEARCH_PHASE5.md
  - docs/AUTORESEARCH_PHASE6.md
  - docs/PHASE_REGISTRY.md
updated_by: codex
updated_at: 2026-04-13
---

# Bounded Autoresearch

## Research question

How does RedThread improve itself without letting autoresearch mutate the very safety systems that control promotion and validation?

## Current synthesis

The current roadmap state is conservative by design.

Two bounded lanes exist:
- **Phase 5 / 7A offense lane** for bounded source mutation over offense modules
- **Phase 6 / 7B defense lane** for bounded defense prompt/template mutation

Both lanes keep:
- explicit accept/reject boundaries
- reversibility via patch artifacts
- promotion discipline
- protected surfaces outside the mutation target set

## Offense lane summary

The bounded offense lane allows controlled changes to offensive modules such as attack algorithms and persona generation.

It explicitly protects:
- evaluation and judge logic
- defense synthesis
- telemetry
- promotion logic
- golden datasets

## Defense lane summary

The bounded defense lane is narrower.

It focuses on defense prompt/template assets rather than broad runtime defense logic. The lane also adds a sealed pre-apply validator so weak or out-of-scope candidates fail closed before normal proposal flow continues.

## Why this matters

This is the core self-improvement story for the current phase of the project.

The project direction is not unrestricted mutation. It is bounded mutation with evidence, reversibility, and promotion gates.

## Contradictions / uncertainty

The broad direction is clear, but the exact future expansion of mutable defense surfaces is intentionally unresolved. The current docs treat any widening beyond prompt/template assets as a later step that should happen only after sustained validation.

## Next questions

- Which additional replay fixtures most improve confidence without expanding unsafe mutation scope?
- What operator-facing evidence views most reduce promotion ambiguity?
- When, if ever, should the defense mutation surface expand beyond prompt/template assets?

## Related pages

- [../decisions/adopt-mempalace-plus-llm-wiki.md](../decisions/adopt-mempalace-plus-llm-wiki.md)
- [../../AUTORESEARCH_PHASE5.md](../../AUTORESEARCH_PHASE5.md)
- [../../AUTORESEARCH_PHASE6.md](../../AUTORESEARCH_PHASE6.md)
- [../../PHASE_REGISTRY.md](../../PHASE_REGISTRY.md)
