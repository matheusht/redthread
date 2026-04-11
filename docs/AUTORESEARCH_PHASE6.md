# Autoresearch Phase 6

Phase 6 formalizes bounded **defense prompt/template mutation** as the second safe autoresearch lane inside Phase 7.

## Goal

Improve defense generation quality without opening live defense runtime logic to mutation.

This phase keeps the existing safety boundaries intact:
- dedicated autoresearch branch
- explicit Phase 3 accept/reject boundary
- reverse patch artifacts and fingerprint validation
- promotion only after explicit research-plane acceptance
- sealed defense-specific pre-apply validation before Phase 3 runs

## Scope

This phase reuses the bounded source mutation worker, but with a defense-only policy and validator.

The explicit mutable/protected split is documented in [docs/DEFENSE_MUTATION_BOUNDARIES.md](docs/DEFENSE_MUTATION_BOUNDARIES.md).

Allowed mutation surface:
- `src/redthread/core/defense_assets.py`
  - `DEFENSE_ARCHITECT_SYSTEM_PROMPT`
  - `DEFENSE_ARCHITECT_USER_TEMPLATE`

Protected surface:
- replay fixtures and replay runner
- validation reporting models
- utility-gate logic
- `BENIGN_DEFENSE_PACK` and benign response heuristics
- `src/redthread/core/defense_synthesis.py`
- evaluation and judge logic
- telemetry
- golden dataset
- memory indexing semantics
- production promotion logic

## Pre-Apply Gate

Every Phase 6 candidate must pass a sealed validation step before it is applied:
- touched lines stay inside the allowed defense prompt symbols
- the structured architect output contract is preserved
- a deterministic jailbreak fixture still renders correctly
- the prompt stays exploit-scoped and avoids broad refusal language

Candidates fail closed. Rejected candidates never enter the normal Phase 3 cycle.

## CLI

Run one bounded defense-prompt cycle:

```bash
./.venv/bin/python -m redthread.cli research phase6 cycle --baseline-first
```

Inspect the latest defense candidate:

```bash
./.venv/bin/python -m redthread.cli research phase6 inspect
```

Revert the latest defense candidate:

```bash
./.venv/bin/python -m redthread.cli research phase6 revert
```

## Proposal Contract

Every Phase 6 proposal must capture:
- mutation phase (`phase6`)
- mutation family
- touched files
- selected tests
- forward patch artifact
- reverse patch artifact
- supervisor decision
- research-plane acceptance state
- promotion eligibility status

## Success Criteria

RedThread can safely:
1. generate one bounded defense prompt mutation
2. validate it before apply with sealed defense checks
3. apply it on the research branch
4. evaluate it through the existing Phase 3 supervisor
5. revert it safely if rejected
6. promote it only after explicit research-plane acceptance

## Next Bounded Steps

After Phase 6, the next finite milestones are:
1. upgrade Phase 6 from prompt-contract checks to richer sealed replay fixtures
2. add defense-specific promotion/revalidation reporting before production promotion
3. only then consider widening the mutable defense surface beyond prompt/template assets
