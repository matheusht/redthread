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

### Next
- wire validation reports into promotion artifacts
- expose report summaries in CLI inspection paths
- add utility gate enforcement before promotion
- expand replay fixtures beyond the starter suite
