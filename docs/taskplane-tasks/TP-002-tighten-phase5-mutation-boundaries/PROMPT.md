# Task: TP-002 — Tighten Phase 5 Mutation Boundaries

**Created:** 2026-04-10
**Size:** M

## Review Level: 3 (Full)

**Assessment:** Safety-boundary change across autoresearch mutation policy, tests, and docs.
**Score:** 6/8 — Blast radius: 1, Pattern novelty: 1, Security: 2, Reversibility: 2

## Canonical Task Folder

```
docs/taskplane-tasks/TP-002-tighten-phase5-mutation-boundaries/
├── PROMPT.md
├── STATUS.md
├── .reviews/
└── .DONE
```

## Mission

Tighten the Phase 5 bounded source-mutation surface so it is actually bounded.

Today, `src/redthread/research/source_mutation_policy.py` allows the broad prefix
`src/redthread/research/`, which exceeds the documented Phase 5 scope and allows
future mutations to touch research files beyond the intended minimal offense-side
surface.

Replace that broad allowance with a narrower explicit allowlist centered on the
real files currently needed by Phase 5, while preserving the existing valid
Phase 5 mutation templates and keeping protected surfaces fail-closed.

## Why This Task Exists

This is the next roadmap-aligned hardening step after restoring the manual
Phase 3 review gate.

It directly follows the repo's stated next priorities:
- tighten mutation boundaries
- keep offense mutation surfaces stable
- preserve explicit safety and promotion boundaries

## Dependencies

- **None**

## Context to Read First

### Tier 2
- `docs/taskplane-tasks/CONTEXT.md`

### Tier 3
- `docs/PHASE_REGISTRY.md`
- `docs/AUTORESEARCH_PHASE5.md`
- `docs/REDTHREAD_STATUS_AUDIT.md`
- `AGENTS.md`

### Source files on the execution path
- `src/redthread/research/source_mutation_policy.py`
- `src/redthread/research/source_mutation_registry.py`
- `src/redthread/research/source_mutation_worker.py`
- `tests/test_research_mutate.py`
- `tests/research_mutation_helpers.py`

## Environment

- **Workspace:** Project root
- **Services required:** None
- **Primary verification:** local/offline only

## File Scope

Expected touch surface should stay narrowly bounded to:
- `src/redthread/research/source_mutation_policy.py`
- `tests/test_research_mutate.py`
- optionally `docs/AUTORESEARCH_PHASE5.md`
- optionally `docs/TASKPLANE_INTEGRATION.md` only if operator guidance must mention the narrowed surface

Do **not** widen the implementation beyond what is needed for the policy hardening.

## Steps

### Step 0: Preflight

- [ ] Read the listed docs and confirm the current Phase 5 documented surface
- [ ] Confirm the current policy mismatch: broad `src/redthread/research/` prefix in `source_mutation_policy.py`
- [ ] Confirm which current Phase 5 templates actually require research-surface access

### Step 1: Narrow the Phase 5 allowlist

- [ ] Replace the broad research prefix allowance with a smaller explicit allowlist
- [ ] Keep current valid Phase 5 template targets working, including `src/redthread/research/prompt_profiles.py`
- [ ] Preserve or strengthen fail-closed behavior for blocked evaluation, telemetry, memory, golden dataset, and promotion surfaces
- [ ] Keep the policy implementation simple and obvious to audit

### Step 2: Strengthen tests around the narrowed boundary

- [ ] Add or update tests that prove allowed current targets still pass
- [ ] Add or update tests that prove unrelated research files are rejected
- [ ] Ensure tests clearly encode the new intended Phase 5 boundary instead of relying on broad prefixes

### Step 3: Align documentation with the real bounded surface

- [ ] Update `docs/AUTORESEARCH_PHASE5.md` if needed so the documented Phase 5 scope matches the implementation
- [ ] Keep wording precise: bounded offense source mutation, not broad research-module mutation

### Step 4: Verification

- [ ] Run targeted mutation tests
- [ ] Run any directly affected research tests needed to validate the policy change
- [ ] Run lint/typecheck only for touched paths when practical

### Step 5: Delivery

- [ ] Summarize the new allowed surface and the blocked examples proven by tests
- [ ] Note any follow-up work discovered but do not widen this task to include it

## Verification Commands

Prefer focused verification first:

```bash
uv run pytest tests/test_research_mutate.py -v
uv run ruff check src/redthread/research/source_mutation_policy.py tests/test_research_mutate.py
```

If needed, expand to:

```bash
uv run pytest tests/test_research_mutate.py tests/test_research_phase3.py -q
uv run mypy src
```

## Documentation Requirements

**Must Update:** `docs/AUTORESEARCH_PHASE5.md` if scope text no longer matches implementation
**Check If Affected:** `docs/TASKPLANE_INTEGRATION.md`

## Completion Criteria

- [ ] Phase 5 policy no longer relies on a broad `src/redthread/research/` prefix
- [ ] Current intended Phase 5 targets still validate successfully
- [ ] Unrelated research files are rejected by policy tests
- [ ] Docs accurately describe the narrowed Phase 5 surface
- [ ] Verification evidence is recorded in STATUS.md

## Git Commit Convention

- **Implementation:** `feat(TP-002): tighten phase5 mutation boundaries`
- **Checkpoints:** `checkpoint: TP-002 <description>`

## Do NOT

- Do not broaden the mutation surface while attempting to "simplify" the policy
- Do not modify promotion logic, daemon logic, or Phase 6 runtime behavior in this task
- Do not add live smoke tests here
- Do not mix this task with replay-fixture or benign-utility work

---

## Amendments (Added During Execution)

<!-- Workers add amendments here if issues discovered during execution. -->
