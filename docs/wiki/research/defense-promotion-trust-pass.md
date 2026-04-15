---
title: Defense + Promotion Trust Pass
type: research
status: complete
summary: Durable research synthesis and completed implementation record for the defense synthesis/validation and promotion/revalidation deep dive.
source_of_truth:
  - docs/DEFENSE_PIPELINE.md
  - docs/PHASE_REGISTRY.md
  - docs/PROGRESS.md
  - docs/SELF_HEALING_HARDENING_PLAN.md
  - docs/wiki/systems/defense-synthesis-and-validation.md
  - docs/wiki/systems/promotion-and-revalidation.md
updated_by: codex
updated_at: 2026-04-15
---

# Defense + Promotion Trust Pass

## Research question

What does RedThread's defense synthesis and validation path actually prove today, and what must still harden before operators should trust promotion and revalidation more deeply?

## Current synthesis

The subsystem is real and already stronger than many other parts of the repo.
It is not only "generate a guardrail and hope".
It already does five important things:
1. isolate the exploit slice
2. generate a narrow defense proposal
3. replay the exploit and benign pack
4. label the evidence class honestly
5. fail closed at promotion time when evidence is weak or incomplete

That means the trust story is no longer vague.
It is now evidence-shaped.
But the evidence is still bounded.

## What is actually proven now

### Defense validation proves
- the tested exploit replay cases were blocked or not blocked
- the tested benign utility prompts were preserved or regressed
- the result carries an explicit evidence class
- replay cases and validation reports persist for later inspection

### Promotion proves
- accepted proposals still face a separate promotion gate
- promotion blocks missing reports, weak evidence, benign regressions, and replay failures
- production memory is not written when the gate fails

## What is not proven now

### Defense validation does not prove
- broad real-world robustness
- broad product utility preservation
- that one live replay suite generalizes to many unseen exploit families

### Promotion does not prove
- a promoted defense is universally safe
- replay coverage is complete
- the system has solved the underlying class forever

Promotion means the current bounded evidence gate passed.
It does not mean the defense became a universal truth.

## Evidence

### Source-doc evidence
- `docs/DEFENSE_PIPELINE.md` says defense generation, replay validation, and later promotion are separate steps
- `docs/wiki/systems/defense-synthesis-and-validation.md` says evidence classes must be read conservatively
- `docs/wiki/systems/promotion-and-revalidation.md` says only `live_replay` is promotable and weak evidence must fail closed
- `docs/SELF_HEALING_HARDENING_PLAN.md` says the next trust gains should come from clearer operator inspection and stronger replay evidence

### Runtime-code evidence
- `src/redthread/core/defense_utility_gate.py` blocks promotion on missing reports, failed exploit blocking, benign regression, non-promotable evidence modes, and missing replay-case evidence
- `src/redthread/research/promotion.py` preserves the explicit research acceptance boundary and only writes production memory after validation succeeds
- `src/redthread/research/promotion_evidence.py` persists operator-facing buckets for missing, weak, and failed evidence

### Test evidence
- `tests/test_defense_truth.py` pins sealed dry-run, live replay, and live validation error as distinct evidence classes
- `tests/test_defense_validation.py` pins the dual requirement: block exploit and preserve benign utility
- `tests/test_research_promotion_validation.py` pins fail-closed promotion behavior for missing reports, weak evidence, benign regressions, and missing replay cases

## Main trust gaps at start of pass

1. **Operator bridge gap**
   - promotion buckets existed
   - validation report detail existed
   - but operators still needed a faster bridge from promotion failure bucket to exact replay-case failure context

2. **Replay breadth gap**
   - replay suite was much better than exact-exploit-only replay
   - but it was still bounded and curated
   - that meant trust was meaningful, not universal

3. **Doc overclaim risk**
   - this subsystem is easy to oversell
   - wiki and operator output needed to keep saying what replay proves and what it does not prove

## Milestones for this pass

### Milestone 1 — Durable research synthesis
Status: complete
- wrote this research page
- updated wiki navigation and log
- kept proof boundaries explicit

### Milestone 2 — Promotion inspection bridge
Status: complete
- promotion inspection now shows trace-level replay-case failure detail for blocked traces
- operators no longer need to jump manually from promotion bucket output to report inspection for the first layer of failure context

### Milestone 3 — Replay breadth pass
Status: complete
- added `exploit_roleplay_probe` to catch training / roleplay framed bypasses
- added `yaml_status_note` to check one more simple structured benign output path
- moved the bounded replay suite to `default-defense-replay-v4`
- updated docs/wiki so the suite change is described honestly

## Approval rule

Only approve what is working.
Every milestone must pass focused tests first, then the local PR-CI mirror.

## Outcome

This pass is complete.

What improved:
- durable wiki research now explains what defense validation and promotion do and do not prove
- promotion inspection now bridges failure buckets to exact replay-case detail
- bounded replay breadth increased with one more exploit variant and one more benign structured-output check

What did not change:
- replay evidence is still bounded
- promotion still means the bounded gate passed, not that the defense is universally safe

## Next questions

- Which replay variants add the most trust per maintenance cost?
- How much operator detail should promotion inspection show before it becomes noisy?
- When is replay breadth strong enough to widen mutable defense scope safely?
