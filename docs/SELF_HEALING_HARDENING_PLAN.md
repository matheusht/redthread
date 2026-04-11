# Self-Healing Hardening Plan

## Goal

Move RedThread from "can generate defenses" to "can validate and promote defenses safely, repeatably, and with evidence."

## Workstreams

### 1. Richer sealed replay validation
- unify replay prompt construction with runtime guardrail injection semantics
- represent replay suites explicitly
- store per-case exploit and benign replay outcomes
- expand beyond the minimal benign pack over time

### 2. Defense-specific reporting
- emit structured validation reports per deployment
- attach replay suite identity, failed cases, and utility summaries
- preserve report data through persistence and promotion artifacts

### 3. Defense utility guarantees
- require exploit blocking and benign preservation
- reject weakly validated or incomplete defense evidence
- promote only defenses with complete validation evidence

### 4. Narrow mutation surfaces
- keep replay, reporting, promotion, and utility-gate code outside mutable defense surfaces
- preserve explicit allowlists and fail-closed validation

## Milestones

### Milestone A
- shared guardrail composition helpers
- dedicated defense replay runner
- structured replay case storage

### Milestone B
- structured defense validation report
- deployment persistence for report data
- CLI/reporting surfacing

### Milestone C
- explicit utility gate and promotability checks
- promotion requires report completeness

### Milestone D
- boundary audit for replay/reporting modules
- negative tests for protected surfaces
- doc/runtime alignment

## Current progress

### Completed in-session
- added shared guardrail composition helpers
- added `DefenseReplayRunner`
- added `ReplayCaseResult`
- refactored `DefenseSynthesisEngine` validation to use the replay runner
- aligned guardrail loader injection with shared composition helper
- preserved replay evidence in memory serialization
- added `DefenseValidationReport`
- wired validation reports into promotion artifacts
- made promotion fail when eligible defense records lack validation reports
- added explicit defense utility gate enforcement in promotion
- made promotion reject non-promotable validation modes, benign regressions, and missing replay-case evidence

### Process log
1. stabilized replay semantics first so validation and injection use the same prompt-shaping path
2. extracted replay execution into dedicated modules before adding more rules
3. introduced structured validation reports so evidence exists independently of markdown summaries
4. wired evidence into promotion artifacts before enforcing a utility gate
5. added utility-gate checks only after report and replay evidence were available
6. expanded targeted tests after each slice to keep the hardening work evidence-backed
7. surfaced validation-evidence failures in CLI promotion output so operators can see why promotion failed
8. marked replay/reporting/utility-gate modules as protected Phase 6 surfaces and added policy tests for them
9. expanded the starter benign replay suite slightly before moving to larger curated fixture sets
10. added a latest-promotion inspection CLI path so operators can inspect evidence without reading raw JSON

### Next
- add CLI inspection for individual deployment validation reports, not just promotion summaries
- split protected replay/report/gate surfaces from mutable defense-prompt surfaces in more explicit docs
- decide whether replay-suite expansion should come from curated fixtures under `tests/` or dedicated runtime fixture artifacts
