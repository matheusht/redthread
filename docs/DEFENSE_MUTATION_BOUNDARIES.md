# Defense Mutation Boundaries

This document makes the Phase 6 mutation boundary explicit.

## Purpose

Phase 6 is allowed to improve **defense prompt/template quality** without gaining the ability to mutate the runtime machinery that validates, reports, persists, or promotes defenses.

That split is the main safety boundary for self-healing hardening.

## Mutable Phase 6 surface

Phase 6 may mutate only:

- `src/redthread/core/defense_assets.py`
  - `DEFENSE_ARCHITECT_SYSTEM_PROMPT`
  - `DEFENSE_ARCHITECT_USER_TEMPLATE`

These are prompt-contract assets. They influence how the Defense Architect reasons and writes candidate clauses, but they do not change replay execution, report structure, memory persistence, or promotion gates.

## Protected Phase 6 surface

Phase 6 must not mutate:

### Replay and evidence
- `src/redthread/core/defense_replay_artifacts.py`
- `src/redthread/core/defense_replay_fixtures.py`
- `src/redthread/core/defense_replay_runner.py`
- `src/redthread/core/defense_reporting_models.py`
- `src/redthread/core/defense_utility_gate.py`

### Deployment and persistence
- `src/redthread/core/defense_synthesis.py`
- `src/redthread/memory/index.py`

### Promotion boundary
- `src/redthread/research/promotion.py`
- `src/redthread/research/promotion_support.py`

### Broad protected prefixes
- `src/redthread/evaluation/`
- `src/redthread/telemetry/`
- `tests/golden_dataset/`

## Why this split exists

The mutable surface may change **how candidate defenses are proposed**.

The protected surface preserves **how candidate defenses are validated and trusted**:
- replay semantics stay sealed
- replay fixtures come from dedicated runtime artifacts, not `tests/`
- validation reports stay structured
- utility gates stay fail-closed
- memory serialization stays stable
- promotion remains evidence-driven

If Phase 6 could mutate both sides at once, it could weaken the very checks meant to constrain it.

## Runtime source of truth

The runtime allow/deny registry lives in:

- `src/redthread/research/defense_mutation_boundaries.py`
- consumed by `src/redthread/research/defense_source_mutation_policy.py`

Tests for this contract live in:

- `tests/test_research_phase6.py`
- `tests/test_defense_mutation_boundaries.py`

## Operator rule

If a future change needs to widen the mutable surface, update all three together:
1. runtime boundary registry
2. policy tests
3. this document

Default stance: fail closed.
