---
title: Current Hardening Tracks
type: research
status: active
summary: Sequential hardening plans for RedThread's current stage: verification, governance, runtime truth, and defense confidence.
source_of_truth:
  - docs/PHASE_REGISTRY.md
  - docs/REDTHREAD_STATUS_AUDIT.md
  - docs/PROGRESS.md
  - program.md
  - README.md
updated_by: codex
updated_at: 2026-04-14
---

# Current Hardening Tracks

## Research question

If RedThread should not prioritize new features right now, what work tracks should be run next, and in what order?

## Current synthesis

The right near-term tracks are:
- Track A — Verification hardening
- Track B — Governance hardening
- Track C — Runtime truth hardening
- Track D — Defense confidence hardening

They should run in that order because each later track depends on trust built by the earlier one.

---

## Track A — Verification hardening

### Why this track comes first

If the truth layer is shaky, every downstream decision is weaker.
This includes:
- campaign scoring
- autoresearch acceptance
- defense quality claims
- promotion confidence

### Goal

Make RedThread's evaluation story honest, green, and inspectable.

### Main targets

1. fix the failing golden regression path
2. calibrate prompt-leak and sensitive disclosure scoring
3. separate sealed fallback behavior from live-judge behavior clearly
4. make pass/fail evidence operator-readable

### Work plan

#### Step A1 — Green the current regression baseline
- reproduce all current failing tests
- isolate whether failure is heuristic, rubric, or judge-path behavior
- patch the smallest safe layer
- rerun the affected suite first, then the full suite

#### Step A2 — Audit evaluation truth boundaries
- document which paths are heuristic fallback only
- document which paths require live providers
- mark what CI proves and what it does not prove

#### Step A3 — Strengthen evaluation evidence
- ensure high-severity prompt leakage stays high-severity
- add or tighten regression coverage where needed
- keep scoring deterministic in sealed paths

### Acceptance criteria
- default regression suite is green
- golden dataset handles clear prompt exfiltration correctly
- docs cleanly distinguish sealed/offline proof from live-provider proof

### Execution note — 2026-04-14
First slice completed:
- sealed golden regression now defaults to offline mode in `tests/test_golden_dataset.py`
- live golden evaluation is now explicit and opt-in via `REDTHREAD_LIVE_GOLDEN=true`
- current local suite result after this slice: `201 passed`
- Phase 6 template drift that blocked the full suite was also corrected so the verification baseline is actually green again

### Risks
- overfitting heuristics to one trace family
- making docs sound stronger than runtime reality again

### Output artifacts to maintain
- test evidence
- updated docs/wiki status pages if truth changed
- log of what the suite proves after the fix

---

## Track B — Governance hardening

### Why this track comes second

Once evaluation is more trustworthy, the next biggest risk is unsafe or ambiguous self-improvement control.

### Goal

Make the research and promotion boundary real, visible, and conservative.

### Main targets

1. restore real operator approval by default
2. tighten mutation allowlists
3. confirm protected surfaces stay protected
4. align docs with actual daemon behavior

### Work plan

#### Step B1 — Audit acceptance flow
- inspect research daemon and supervisor acceptance path
- identify all auto-accept or auto-reject paths
- classify which are acceptable defaults and which are governance bugs

#### Step B2 — Harden the boundary
- require manual acceptance by default where claims say manual gate exists
- make any automation opt-in and explicit
- preserve clear artifacts for accept, reject, revert, and promote

#### Step B3 — Tighten mutation scope
- replace broad path rules with narrow allowlists where possible
- confirm judge, telemetry, promotion, replay evidence, and utility gates remain protected

#### Step B4 — Fix trust language
- update docs so approval and boundedness claims match runtime truth exactly

### Acceptance criteria
- operator boundary is explicit and default-safe
- mutation surfaces are narrow and inspectable
- docs no longer overstate approval behavior

### Risks
- hardening the gate may slow experimentation
- hidden automation paths may exist in multiple modules

### Output artifacts to maintain
- governance docs
- mutation boundary docs
- research workflow notes and wiki updates

### Execution note — 2026-04-14
Governance audit completed.
Findings and follow-through:
- current daemon code already leaves new proposals in `awaiting_review` instead of auto-accepting or auto-rejecting them
- README guidance was updated so the documented boundary now matches the runtime truth: manual Phase 3 review is the default control point
- no new auto-finalization path was found in the bounded research loop; interrupted promotion resume remains tied to an already-started explicit promotion flow

---

## Track C — Runtime truth hardening

### Why this track comes third

After truth and governance improve, the next question is whether the real execution path behaves as claimed.

### Goal

Make RedThread's offline and live runtime stories both honest and useful.

### Main targets

1. truly offline dry-run
2. small opt-in live smoke suite
3. clear operator evidence for what runtime path was exercised

### Work plan

#### Step C1 — Seal dry-run
- identify all codepaths still touching provider setup or live runtime state during dry-run
- replace with local-only shims or deterministic paths where safe
- verify no accidental provider dependency remains for sealed validation use

#### Step C2 — Add a live smoke path
- create a tiny, environment-gated path for real provider/runtime verification
- keep it cheap, explicit, and separate from sealed CI

#### Step C3 — Clarify runtime evidence
- show whether a run was sealed dry-run, simulated fallback, or live-provider execution
- keep transcripts and reports explicit about mode

### Acceptance criteria
- dry-run is truly offline for its intended path
- there is a small live smoke check proving the real path end to end
- docs and CLI language describe execution mode honestly

### Risks
- dry-run sealing may expose hidden coupling in persona generation or target setup
- live smoke tests may become flaky if not tightly scoped

### Output artifacts to maintain
- runtime mode docs
- smoke-test evidence
- transcript/report mode labels

### Execution note — 2026-04-14
Runtime truth hardening completed for the sealed campaign path.
Changes:
- `redthread run --dry-run` now stays offline for campaign execution by using deterministic dry-run personas and lazy attacker/target construction
- post-campaign telemetry no longer touches live runtime paths during dry-run
- transcripts now record explicit `runtime_mode` and `telemetry_mode` labels so operators can see whether a run was sealed or live-backed
- new regression coverage proves the dry-run engine path stays offline while still producing artifacts

---

## Track D — Defense confidence hardening

### Why this track comes fourth

This track depends on the earlier tracks because defense confidence means little if evaluation, governance, and runtime mode are still ambiguous.

### Goal

Make RedThread's self-healing claims stronger through richer replay evidence and clearer benign-utility proof.

### Main targets

1. deepen replay fixture coverage
2. strengthen benign utility preservation checks
3. improve defense-specific promotion evidence
4. keep the mutable defense surface narrow until confidence is sustained

### Work plan

#### Step D1 — Expand replay evidence carefully
- add curated runtime fixtures where current replay coverage is thin
- preserve sealed replay surfaces as protected assets

#### Step D2 — Improve utility proof
- strengthen benign response expectations
- make regressions against utility visible in reports

#### Step D3 — Improve operator inspection
- keep validation reports easy to inspect before any promotion decision
- make failed case IDs and replay context easy to trace

#### Step D4 — Re-evaluate mutation scope only after evidence
- widen defense mutation only if replay and utility evidence stay strong over time
- default remains conservative

### Acceptance criteria
- richer replay evidence exists for key defense paths
- benign utility regressions are easier to detect and explain
- promotion decisions can rely on defense-specific evidence, not vague summaries

### Risks
- broader replay suites can bloat maintenance if they are not curated
- utility checks can become too weak or too broad if not scoped carefully

### Output artifacts to maintain
- defense validation reports
- promotion evidence docs
- wiki pages describing defense confidence truthfully

### Execution note — 2026-04-14
Defense confidence hardening completed with richer replay evidence and clearer operator inspection.
Changes:
- the sealed defense replay suite now covers two additional benign utility cases (`bullet_summary`, `translation_check`) to widen post-patch utility proof
- validation reports now persist replay-case counts, benign pass counts, and per-case failure reasons
- report inspection output now surfaces those counts and reasons directly so failed promotions are easier to diagnose
- full suite result after Tracks A-D: `203 passed`

---

## Recommended execution order

1. Track A — Verification hardening
2. Track B — Governance hardening
3. Track C — Runtime truth hardening
4. Track D — Defense confidence hardening

## What should wait until after these tracks

- new major attack algorithms
- broader defense mutation surfaces
- UI polish
- enterprise packaging work
- more autonomy for autonomous self-editing

## Current answer

RedThread should spend its next cycle making the current machine more trustworthy, not more feature-rich.
