# RedThread Status Audit

Date: 2026-04-09

## Purpose

This document answers four practical questions:

1. Is RedThread fully complete?
2. Have all currently defined phases been implemented?
3. Is the end-to-end workflow present and working?
4. What should we stop building, and what should we harden next?

This is a reality check against the live repository, not just the roadmap.

---

## Executive Answers

### Is RedThread fully complete?

No.

RedThread is feature-rich and architecturally broad, but it is not fully complete in the sense of:

- fully verified end-to-end on live backends
- fully aligned between docs and runtime behavior
- fully hardened for autonomous safe self-improvement
- fully proven as a production-grade closed-loop system

It is better described as:

- phase-complete on paper through the currently defined Phase 7B scope
- partially verified in tests
- operationally promising
- still in a hardening and truth-alignment stage

### Have all phases in `docs/PHASE_REGISTRY.md` been implemented?

Yes, according to the current registry, Phases 1 through 7B are implemented.

That is true in the narrow sense that the codepaths, CLI entrypoints, tests, and docs for those phases exist.

That is not the same thing as saying the system is finished.

The registry itself still lists next bounded steps after Phase 7B:

1. deepen Phase 6 with richer sealed replay fixtures
2. add defense-specific promotion and revalidation reporting
3. harden end-to-end defense utility guarantees
4. only then consider widening mutable defense surfaces

So the project has implemented all currently enumerated phases, but it has not reached a "nothing important left to do" state.

### Is the end-to-end workflow present?

Yes.

The intended workflow exists in code:

1. run campaign
2. generate personas
3. execute attacks
4. judge results
5. optionally synthesize defenses
6. write transcripts and memory artifacts
7. run bounded autoresearch lanes
8. emit Phase 3 proposals
9. accept or reject in research
10. promote accepted research outputs to production memory

### Is the end-to-end workflow fully proven working?

No.

What is true today:

- The workflow exists structurally.
- Most unit tests pass.
- Lint passes.
- Type checking passes.
- CLI entrypoints exist for campaign, monitor, dashboard, phase3, phase4, phase5, phase6, daemon, and promotion.

What is also true today:

- `make test` is not green: 155 passed, 1 failed.
- The local dry-run campaign still touched PyRIT/OpenAI runtime paths and attempted real provider access.
- The CI "golden regression" runs under `REDTHREAD_DRY_RUN=true`, so it is not a true live-model regression gate.

The correct statement is:

RedThread has an end-to-end architecture, but not a fully proven end-to-end production validation story.

---

## What Is Real Today

### Working capability surface

The repository contains real implementations for:

- PAIR
- TAP
- Crescendo
- GS-MCTS
- LangGraph supervisor orchestration
- guardrail synthesis and sandbox replay
- telemetry and ASI
- monitor daemon
- dashboard and CLI
- bounded Phase 4 runtime mutation
- bounded Phase 5 offense source mutation
- bounded Phase 6 defense prompt mutation
- research promotion artifacts and checkpoints

### Verification signals that are actually strong

- `make lint` passes clean.
- `make typecheck` passes.
- Most of the unit suite passes.
- There are explicit tests for:
  - core algorithms
  - supervisor routing
  - defense synthesis
  - guardrail loader
  - telemetry
  - research mutation lanes
  - promotion behavior
  - research daemon behavior

### Verification signals that are weaker than they look

- `make typecheck` passes, but `pyproject.toml` still ignores errors in several important legacy modules.
- `make test` is not fully green.
- golden regression in CI is run with `REDTHREAD_DRY_RUN=true`
- `EvaluationPipeline` falls back to heuristic scoring in dry-run and on judge failure
- local dry-run still goes through persona generation and runtime target setup, so it is not a fully sealed offline path

---

## Evidence Summary

### 1. Phase coverage

`docs/PHASE_REGISTRY.md` marks 1 through 7B complete.

Conclusion:

- implemented phase coverage: yes
- finished project: no

### 2. Unit and quality status

Observed locally:

- `make lint`: passed
- `make typecheck`: passed
- `make test`: failed with 1 failing test in `tests/test_judge.py`

Failure:

- `test_full_evaluation_mocked`
- reason: `judge._judge_llm` is `None` when the test tries to stub `.send`

Conclusion:

- the repo is close to green, but not green
- "fully complete" is too strong while the standard unit gate still fails

### 3. Dry-run reality

A local CLI dry-run reached:

- engine startup
- guardrail loader
- supervisor invoke
- persona generation

It then attempted real runtime setup and provider access:

- PyRIT local DB initialization
- OpenAI connection during persona generation

Conclusion:

- the campaign path is real
- dry-run is not fully offline
- environment readiness still matters even for validation runs

### 4. Golden regression reality

The CI workflow runs golden regression with `REDTHREAD_DRY_RUN=true`.

The evaluation pipeline explicitly uses heuristic scoring in dry-run, and also falls back heuristically on judge failure.

Conclusion:

- the golden suite is useful as a sealed offline consistency gate
- it is not a strong live-model truth gate in CI as currently configured
- claims about mathematically proven live judge behavior should be framed carefully

---

## Where Docs and Runtime Do Not Match

### 1. Operator approval is weaker in practice than claimed

Docs repeatedly describe explicit research-plane accept/reject control.

However, the research daemon auto-finalizes proposals by calling accept or reject based on the supervisor recommendation.

Why this matters:

- the docs describe an operator boundary
- the daemon currently weakens that boundary inside the research plane
- this is exactly the kind of mismatch that becomes dangerous if autonomy is widened further

### 2. Decision-tree docs are stale

`docs/AGENT_DECISION_TREE.md` points to several docs that do not exist under those names.

Why this matters:

- the navigation layer is not reliable
- architecture decisions can drift if source-of-truth docs are stale

### 3. Repo engineering standards are not fully enforced

Your repo-level standard says no component, hook, or module should exceed 200 lines.

Current live violations include:

- `src/redthread/cli.py`
- `src/redthread/core/mcts.py`
- `src/redthread/core/tap.py`
- `src/redthread/core/crescendo.py`
- `src/redthread/core/pair.py`
- `src/redthread/core/defense_synthesis.py`
- `src/redthread/research/models.py`

Why this matters:

- larger files increase mutation risk
- they reduce confidence in autonomous or bounded code-edit loops
- the project should either enforce this rule or relax it honestly

### 4. Phase 5 mutation scope is broader than the narrative suggests

Phase 5 is described as bounded offense-side mutation.

But the allowlist currently includes the entire `src/redthread/research/` prefix except for a few blocked files.

Why this matters:

- this includes parts of the self-improvement machinery itself
- it is more autonomy than the docs imply
- widening beyond this before hardening governance would be a mistake

---

## What Not To Do

These are the highest-confidence non-goals for the current stage.

### Do not add free-form self-editing over core Python

Do not let the agent freely rewrite:

- `core/`
- `evaluation/`
- `telemetry/`
- `promotion/`
- defense runtime logic

Why:

- the project still has doc/runtime mismatch
- one research gate is weaker than advertised
- offline validation is stronger than live validation today
- larger modules make autonomous edits riskier

### Do not add another major attack algorithm right now

Do not prioritize a new jailbreak/search family before:

- fixing verification gaps
- tightening research-plane governance
- hardening Phase 6 replay
- proving benign-utility preservation better

Why:

- the registry already says the direction is safe self-improvement, not attack-surface expansion
- more attack breadth will not solve the current trust gap

### Do not treat CI golden regression as proof of live-model behavior

It is currently a useful sealed regression gate, not a true live-judge proof.

### Do not widen defense mutation beyond prompt assets yet

Phase 6 is still intentionally conservative.

Widening to live defense logic now would be premature.

### Do not keep claiming explicit human approval if daemon auto-accept remains

Either:

- change the daemon
- or change the docs

Do not leave them inconsistent.

### Do not invest in UI or enterprise integration before runtime hardening

The product is still fundamentally a CLI-first research/security engine.

The next value comes from reliability, not presentation.

---

## What We Should Do Next

Priority is ordered by ROI and risk reduction.

### 1. Make the repo fully green

Fix the failing judge test first.

Reason:

- no serious "fully complete" claim should be made while the default test suite is red

### 2. Restore the real operator boundary

Change the research daemon so proposal acceptance is manual by default, or explicitly configurable.

Reason:

- this is the biggest governance mismatch in the repo

### 3. Tighten Phase 5 mutation scope

Replace the broad `src/redthread/research/` prefix with a narrower allowlist.

Reason:

- bounded mutation should actually be bounded

### 4. Add a real live smoke test path

Create a small, opt-in, environment-gated live smoke suite that proves:

- persona generation
- attack execution
- judge evaluation
- defense synthesis
- promotion replay

Reason:

- current tests mostly prove architecture and offline logic
- they do not fully prove live provider workflow

### 5. Make dry-run truly offline

Dry-run should not require:

- provider reachability
- PyRIT DB paths outside the repo
- runtime model setup for sealed validation

Reason:

- dry-run should be the safest operator validation path

### 6. Deepen Phase 6 exactly as the roadmap says

Best next bounded milestone:

- richer sealed replay fixtures
- stronger benign-utility checks
- defense-specific promotion reports

### 7. Clean documentation drift

Fix:

- stale decision tree doc targets
- operator-approval wording
- any claims that overstate live validation

### 8. Resolve the 200-line rule honestly

Pick one:

- enforce the rule and refactor oversized modules
- or relax the rule and document a realistic threshold

Do not keep a rule that the live repo does not follow.

---

## Standard Guidelines: What We Say vs What We Actually Do

### Standards that are clearly present in the codebase

- RPI workflow
- bounded mutation philosophy
- strong separation between research and production promotion
- protected mutation surfaces for judge, telemetry, golden data, and promotion
- async-first architecture
- typed models and structured artifacts

### Standards that are only partially real today

- strict human gate in research
- strict file-size discipline
- fully strict mypy across the whole repo
- live-model regression proof in CI
- fully offline dry-run

### What this means

The project does have a real engineering philosophy.

The problem is not lack of architecture.
The problem is that some high-level standards are ahead of the runtime truth.

The next stage should be narrowing that gap.

---

## Is RedThread Useful Right Now?

Yes, in the right context.

It is useful today as:

- a local or staging red-team engine
- a bounded autoresearch platform
- a guardrail synthesis research harness
- a decision-support tool for prompt and defense hardening

It is not yet ideal as:

- a fully autonomous production self-improving agent
- a trust-minimized production promotion system
- a fully proven continuous red-team daemon with no operator ambiguity

---

## Ideal Use Case

The ideal current use case is:

Run RedThread against a staging or internal agent where:

- the system prompt and objective are known
- an operator can review outputs
- local models or API keys are available
- bounded mutation and proposal review are acceptable
- the goal is to discover weaknesses, generate candidate defenses, and iteratively harden them

Best-fit scenario:

- security engineering or AI platform team
- testing a customer-support, internal-assistant, or workflow agent
- using RedThread to compare attack success before and after prompt/guardrail changes
- using Phase 5 and Phase 6 to improve prompts and bounded attack assets in a research branch

Not the best-fit scenario right now:

- unattended production self-editing
- direct autonomous mutation of defense runtime logic
- autonomous promotion to production without strong human review

---

## Final Bottom Line

RedThread is not a fake project and it is not just a phase-labeled scaffold.

It has real architecture, real bounded autoresearch machinery, real promotion artifacts, real monitoring pieces, and a broad test surface.

But it is not fully complete.

The right framing is:

- phase-complete through the currently defined roadmap
- not yet fully hardened
- not yet fully truth-aligned between docs, tests, and runtime
- worth continuing
- should now prioritize reliability, governance, and verification over more autonomy

If scope must be cut, cut this first:

- free-form self-writing core code
- new attack algorithms
- UI polish
- premature enterprise integration

If effort must be focused, focus here:

- green test suite
- real human gate
- tighter mutation scope
- live smoke validation
- deeper Phase 6 replay and benign-utility guarantees
