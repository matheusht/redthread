# TP-002: Tighten Phase 5 Mutation Boundaries — Status

**Current Step:** Not Started
**Status:** 🔵 Ready for Execution
**Last Updated:** 2026-04-10
**Review Level:** 3
**Review Counter:** 0
**Iteration:** 0
**Size:** M

---

### Step 0: Preflight
**Status:** ⬜ Not Started

- [ ] Read roadmap and Phase 5 scope docs
- [ ] Confirm the broad `src/redthread/research/` allowance in `source_mutation_policy.py`
- [ ] Confirm current valid template targets that must remain allowed

---

### Step 1: Narrow the Phase 5 allowlist
**Status:** ⬜ Not Started

- [ ] Replace broad research-prefix allowance with narrower explicit allowed targets
- [ ] Preserve current valid targets, including `src/redthread/research/prompt_profiles.py`
- [ ] Preserve fail-closed blocked surfaces and keep policy easy to audit

---

### Step 2: Strengthen tests around the narrowed boundary
**Status:** ⬜ Not Started

- [ ] Prove allowed targets still pass
- [ ] Prove unrelated research files are rejected
- [ ] Encode the new intended boundary directly in tests

---

### Step 3: Align documentation with the real bounded surface
**Status:** ⬜ Not Started

- [ ] Update `docs/AUTORESEARCH_PHASE5.md` if needed
- [ ] Check whether `docs/TASKPLANE_INTEGRATION.md` needs a scope note

---

### Step 4: Verification
**Status:** ⬜ Not Started

- [ ] Run targeted mutation tests
- [ ] Run touched-path lint checks
- [ ] Record verification evidence

---

### Step 5: Delivery
**Status:** ⬜ Not Started

- [ ] Summarize the new allowlist and blocked examples
- [ ] Capture follow-up items without widening scope

---

## Reviews

| # | Type | Step | Verdict | File |
|---|------|------|---------|------|

---

## Discoveries

| Discovery | Disposition | Location |
|-----------|-------------|----------|

---

## Execution Log

| Timestamp | Action | Outcome |
|-----------|--------|---------|
| 2026-04-10 | Task staged | PROMPT.md and STATUS.md created |

---

## Blockers

*None*

---

## Notes

This task intentionally focuses only on narrowing the Phase 5 mutation boundary.
