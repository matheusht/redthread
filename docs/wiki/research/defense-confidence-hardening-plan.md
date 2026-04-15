---
title: Defense Confidence Hardening Plan
type: research
status: active
summary: Research-backed execution plan for the defense synthesis, validation, and promotion deep dive.
source_of_truth:
  - docs/DEFENSE_PIPELINE.md
  - docs/PHASE_REGISTRY.md
  - docs/PROGRESS.md
  - docs/REDTHREAD_STATUS_AUDIT.md
  - docs/wiki/systems/defense-synthesis-and-validation.md
  - docs/wiki/systems/promotion-and-revalidation.md
  - docs/wiki/systems/subsystem-focus-map.md
  - docs/wiki/research/current-hardening-tracks.md
  - docs/SELF_HEALING_HARDENING_PLAN.md
updated_by: codex
updated_at: 2026-04-15
---

# Defense Confidence Hardening Plan

## Research question

After evaluation and telemetry truth hardening, what is the highest-value next trust pass for RedThread's self-healing loop?

## Current synthesis

The next deep dive should target:
- defense synthesis and validation
- promotion and revalidation evidence

Why this wins now:
- source docs already put defense confidence next in line after verification, governance, and runtime truth
- RedThread's core differentiator is not just finding jailbreaks, but validating and promoting narrow fixes safely
- the subsystem has real structure now, but its evidence classes are still less explicit than the evaluation subsystem

## Current runtime picture

### Strong parts already present
- `DefenseSynthesisEngine` isolates, generates, validates, and builds structured deployment records
- `DefenseReplayRunner` stores exploit and benign replay cases separately
- `DefenseValidationReport` persists operator-facing replay summaries
- promotion rejects weak evidence such as missing reports, benign regressions, missing replay-case evidence, and dry-run validation
- CLI inspection already surfaces validation reports from research and production memory

### Main truth gaps still worth hardening
1. defense evidence classes are still too implicit
2. replay suite breadth is still limited even though it is better than before
3. promotion confidence depends on replay evidence quality, not just on promotion logic quality
4. docs/wiki for defense evidence are still thinner than the newer evaluation and telemetry truth docs

## Evidence

### Source-doc evidence
- `docs/wiki/research/current-hardening-tracks.md` says defense confidence hardening is Track D and should deepen replay coverage, utility checks, and promotion evidence clarity
- `docs/wiki/systems/subsystem-focus-map.md` says defense synthesis and validation now matter most for replay depth, benign utility preservation, and promotion evidence readability
- `docs/PROGRESS.md` says the next finite milestones are more live validation, stronger operator inspection, and doc alignment before widening mutable defense scope

### Runtime-code evidence
- `src/redthread/core/defense_synthesis.py` still compresses multiple evidence realities into a small set of fields, especially around validation outcomes
- `src/redthread/core/defense_replay_runner.py` distinguishes dry-run and live validation mode, but not the full operator trust meaning of each result class
- `src/redthread/core/defense_utility_gate.py` currently keys promotability on `validation_mode`, which is useful but still coarser than explicit evidence strength
- `src/redthread/research/promotion.py` is fail-closed, but the strength of promotion truth still depends on the quality and clarity of the defense evidence beneath it

## Contradictions / uncertainty

What is already true:
- the subsystem is much safer and more inspectable than it was before
- promotion discipline is meaningfully stronger now

What is not yet fully settled:
- how explicit defense evidence classes should be named and persisted
- how wide the replay suite should become before maintenance cost outweighs trust gain
- how much live replay evidence is enough before a defense can be described as strong rather than merely acceptable

## Milestones

### Milestone 1 — Defense evidence modes
Goal:
- separate sealed dry-run replay, successful live replay, and live validation failure as different evidence classes

Why it matters:
- today these paths are not as explicit as the evaluation subsystem's evidence modes
- operators and promotion logic should not read them as equally strong

Planned work:
- add explicit defense evidence metadata to validation results and reports
- surface evidence mode in CLI/report inspection
- tighten promotion utility gate so promotability depends on strong evidence class, not only coarse validation mode
- add regression tests for sealed dry-run evidence, successful live replay evidence, and live validation failure evidence
- update defense wiki/docs to explain the truth boundary clearly

Acceptance criteria:
- defense results label sealed dry-run vs successful live replay vs live validation failure explicitly
- promotion rejects non-promotable defense evidence classes cleanly
- docs/wiki explain what each evidence class proves and does not prove

### Milestone 2 — Replay suite confidence hardening
Goal:
- strengthen confidence that replay evidence is broad enough to catch narrow-fix vs over-refusal problems

Planned work:
- inspect default replay suite blind spots
- pin edge cases for utility preservation and exploit blocking
- expand replay artifacts only where evidence is thin
- keep runtime fixture artifacts curated and bounded

Acceptance criteria:
- replay suite covers the highest-risk defense confidence gaps more explicitly
- regressions around over-broad refusal or weak exploit blocking are pinned
- docs/wiki describe replay breadth honestly

### Milestone 3 — Promotion evidence hardening
Goal:
- make promotion decisions easier to trust and easier to inspect

Planned work:
- strengthen promotion summaries and failure reasons
- ensure operators can quickly see weak evidence, missing evidence, and failed evidence
- keep promotion discipline clearly separate from mutation generation

Acceptance criteria:
- promotion failures point to the exact missing or weak evidence class
- CLI/operator output is easier to inspect without opening raw JSON manually
- docs/wiki explain promotion evidence as evidence, not magic approval

### Milestone 4 — Structural cleanup for safer future edits
Goal:
- reduce file-size and mixed-responsibility risk inside the defense confidence path

Planned work:
- split oversized defense and promotion modules where needed
- split oversized tests where needed
- keep reporting, replay, gating, and orchestration responsibilities more isolated

Acceptance criteria:
- touched files move closer to repo size and separation rules
- future hardening work becomes safer and lower-context

## Open questions

### Gap check
- Security / red-teaming coverage: replay hardening must not collapse to single easy benign checks only; exploit replay plus benign preservation both need to stay first-class
- Evaluation metrics: the defense path still relies on judge-derived exploit scoring during live replay, so evidence hardening must keep that judgment path visible
- Defense pipeline continuity: the loop must remain isolate -> generate -> validate -> promote, with truth labels added instead of hidden shortcuts

## Immediate next move

Start Milestone 1.

Reason:
- it is the narrowest, highest-leverage truth fix
- it improves operator understanding and promotion correctness before replay breadth expansion
- it gives the later milestones a cleaner evidence vocabulary to build on
