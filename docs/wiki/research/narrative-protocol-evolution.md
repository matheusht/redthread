---
title: Narrative Protocol Evolution
type: research
status: active
summary: Investigation into whether RedThread should formalize a first-class narrative adaptation layer on top of Crescendo, MCTS, and persona strategy generation. A minimal MVP (NarrativeState + NarrativeAdaptationPolicy) has been implemented as a bounded Crescendo enhancement.
source_of_truth:
  - docs/algorithms.md
  - docs/PHASE_REGISTRY.md
  - docs/AUTORESEARCH_PHASE5.md
  - docs/REDTHREAD_STATUS_AUDIT.md
  - src/redthread/core/crescendo.py
  - src/redthread/core/narrative_models.py
  - src/redthread/core/narrative_policy.py
  - src/redthread/core/mcts.py
  - src/redthread/core/mcts_helpers.py
  - src/redthread/core/pair.py
  - src/redthread/personas/generation_support.py
  - src/redthread/personas/generator.py
updated_by: codex
updated_at: 2026-04-23
---

# Narrative Protocol Evolution

## Research question

Should RedThread add a first-class narrative adaptation layer that explicitly tracks and evolves multi-turn attack protocols during a campaign?

## Current status

**MVP implemented as a bounded Crescendo enhancement.**

Two new files added to `src/redthread/core/`:
- `narrative_models.py` — `NarrativePhase`, `NarrativeState`, `NarrativeGuidance` (pure Pydantic data)
- `narrative_policy.py` — `NarrativeAdaptationPolicy` (deterministic, no LLM calls)

Integration: `CrescendoAttack.run()` now initializes a `NarrativeState`, calls `policy.recommend()` before each turn, injects guidance into the attacker prompt, and calls `policy.update()` after each accepted turn. Final state is serialized into `trace.metadata["narrative_state"]`.

All 22 tests green. `make ci` passes.

---

## Proposed idea (original)

The candidate concept was a small engine or helper that starts from:
- target description
- initial narrative seed
- persona cover story
- allowed strategies

Then adapts the attack protocol based on:
- target refusals
- target partial compliance
- successful framings
- failed framings
- conversational phase progression

The output would not just be the next prompt.
It would be a compact evolving protocol such as:
- current phase
- preferred framing
- pivot rules
- escalation path
- motifs to reuse
- motifs to avoid

## Current overlap in RedThread

RedThread already had major partial overlap before the MVP:

### PAIR
PAIR refines prompts from target response, score, and feedback.
Adaptive, but mostly linear and prompt-local.

### Crescendo
Crescendo is the closest current match.
It keeps client-side conversation history, escalates gradually, and retries from a different angle after refusals.
**The MVP inserts narrative adaptation directly here.**

### GS-MCTS
GS-MCTS already performs strategy-guided planning and reward-driven path preference.
This is close to protocol search, but strategy labels are still thinner than a full narrative protocol abstraction.

### Persona generation
Personas already include:
- cover story
- hidden objective
- system prompt
- allowed strategies

This gives RedThread a natural seed layer for narrative adaptation.
**The MVP reuses `derive_strategies(persona)` from `mcts_helpers.py` as the strategy pool.**

## What the MVP adds

`NarrativeState` tracks across Crescendo turns:
- current phase: `rapport → legitimacy → pressure → ask`
- used, successful, and failed strategies
- pivot count per phase
- consecutive failures
- last refusal signal

`NarrativeAdaptationPolicy` (deterministic, 6 rules):
1. Low score + refusal → mark strategy failed, pivot, hold phase
2. Low score, no refusal → mark failed, soften framing, hold phase
3. Medium score → hold phase, encourage gradual pressure
4. High score → mark successful, advance phase
5. 2+ pivots fail same phase → force phase advance
6. All strategies exhausted → generic escalation fallback

Guidance is injected into attacker prompt as:
```
## Narrative Guidance
Phase action: escalate
Strategy: invoke urgency of deadline
Framing: Begin introducing time pressure or organizational need.
Avoid: claim executive authority
```

Disable with `REDTHREAD_NARRATIVE_ADAPTATION_ENABLED=false`.

## What is still missing

RedThread does not yet have:
- cross-campaign motif memory (durable successful narrative patterns across runs)
- reusable protocol export ("this target responds best to audit-pretext → empathy pivot")
- target-specific narrative playbooks
- semantic refusal detection (current MVP uses keyword heuristics)

## Why a standalone engine is still premature

The current project direction after GS-MCTS is bounded self-improvement and trust hardening, not attack-family sprawl.

A large standalone new algorithm would be too much right now.

The audit doc ([docs/REDTHREAD_STATUS_AUDIT.md](../../REDTHREAD_STATUS_AUDIT.md)) explicitly warns:
> "Do not add another major attack algorithm right now."

## Potential Phase 2

MCTS protocol priors:
- sample richer protocol bundles (full narrative arcs) instead of plain strategy strings
- replace `strategy: str` on `MCTSNode` with a richer `NarrativeProtocol` object

## Potential Phase 3

Bounded motif mining:
- mine winning traces for narrative motifs
- store as bounded research artifact
- operator-reviewed only (follows Phase 5 / Phase 6 gate pattern)

Both phases fit the repo direction better once the MVP is validated.

## Contradictions / uncertainty

- It is not yet proven that a formal protocol object beats current Crescendo heuristics enough to justify extra complexity.
- The exact storage boundary is unresolved for cross-campaign memory: campaign-local only (current) vs. durable MemPalace motifs (future).
- Refusal detection is keyword-based in MVP. Semantic detection (embedding similarity to known refusal patterns) would be stronger but is overkill for MVP.

## Next questions

1. Does the narrative guidance noticeably improve near-miss rate or reduce dead-end retry chains in live runs?
2. Should MCTS sample richer narrative protocol priors instead of simple strategy strings (Phase 2)?
3. Should successful narrative motifs become a bounded autoresearch artifact later (Phase 3)?

## Related pages

- [bounded-autoresearch.md](bounded-autoresearch.md)
- [../systems/orchestration-and-engine-runtime.md](../systems/orchestration-and-engine-runtime.md)
- [../timelines/redthread-phase-evolution.md](../timelines/redthread-phase-evolution.md)
- [../../AUTORESEARCH_PHASE5.md](../../AUTORESEARCH_PHASE5.md)
- [../../PHASE_REGISTRY.md](../../PHASE_REGISTRY.md)
- [../../REDTHREAD_STATUS_AUDIT.md](../../REDTHREAD_STATUS_AUDIT.md)
