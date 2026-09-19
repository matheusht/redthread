# Open-issue production readiness and launch review specification

## Problem Statement

Operators need reliable authorization, replay evidence, orchestration, evaluation, storage, and launch-review reports. The intake snapshot contains twenty Wave 2 implementation tickets, their tracking map, and the launch-readiness proposal. Existing interfaces and promotion boundaries must remain compatible while every requested gap is addressed.

## Solution

Complete the remaining authorized intake as one verified change set, using existing execution and reporting paths. Record source-backed research, decisions, implementation evidence, and remaining uncertainty in the project wiki. A named launch-readiness preset should run normal campaigns and summarize evidence without implying universal safety or automatic promotion.

## User Stories

1. As a maintainer, I want evaluation orchestration, heuristics, and metrics separated so each remains auditable.
2. As an integrator, I want model decomposition to preserve existing imports so callers remain compatible.
3. As an operator, I want invalid action arguments rejected before execution so capability grants cannot authorize arbitrary inputs.
4. As an operator, I want authoritative sensitivity checks so callers cannot downgrade protected resources.
5. As an operator, I want reconnaissance, social analysis, and exploit preparation wired into the supervisor so their outputs reach attack execution.
6. As a reviewer, I want live judge failures identified as degraded evidence so heuristic results cannot masquerade as live confirmation.
7. As an operator, I want SQLite telemetry writes to tolerate concurrent readers and writers.
8. As an operator, I want cross-process memory writes serialized so concurrent campaigns cannot corrupt evidence.
9. As an operator, I want scoped guardrail clauses loaded across common Markdown and newline formats.
10. As an operator, I want replay bundles executable from the CLI with clear results and failing exit codes.
11. As a launch reviewer, I want a named launch-readiness preset mapped to existing campaign settings.
12. As a launch reviewer, I want executive findings before detailed evidence, including scope, uplift, replay, utility, evidence class, and defense state.
13. As a launch reviewer, I want ready, conditional, or blocked gate decisions tied to observed evidence.
14. As a launch reviewer, I want fallback-only evidence treated as diagnostic and non-promotable.
15. As a launch reviewer, I want a sanitized external packet or explicit placeholder so raw secrets are not shared accidentally.
16. As a maintainer, I want source-backed wiki records and reproducible verification so future work can distinguish proven behavior from assumptions.

## Implementation Decisions

- Reuse existing public interfaces and normal campaign execution. Preserve model identity and backward-compatible imports during decomposition.
- Keep each changed runtime module at or below two hundred lines, with the tighter component budgets requested by architecture tickets where applicable.
- Fail closed at authorization boundaries. Parameter validation and authoritative sensitivity form one coherent policy contract; new least-agency presets are externally owned. Existing presets receive scalar schemas needed to preserve their authorized calls.
- Keep dry-run, sealed, live, and degraded judge evidence distinct. Exceptions must not upgrade evidence or activate defenses.
- Specialized-agent results must be consumed by the existing attack path. Worker timeout changes are externally owned.
- Use standard-library locking and SQLite concurrency controls; avoid new infrastructure.
- Treat unavailable scope, uplift, replay, and utility evidence as unknown, never as success.
- Preserve human-controlled guardrail activation. Launch readiness is an evidence review, not a safety certification.
- Expose the preset as `redthread run --preset launch-readiness`. Run PAIR, TAP, and Crescendo through the normal engine, retain standard per-strategy reports, and put an aggregate executive decision before the detailed findings.
- Clean traces need distinct baseline target replay and benign utility evidence; use the existing bounded replay runner without generating, indexing, or activating a defense. Preserve target prompt scope and its hash. A baseline replay is not a second live JudgeAgent verdict. Confirmed findings require their matching defense validation records; baseline evidence cannot substitute for patched-defense proof.
- Research artifacts refine implementation details before each bounded implementation batch. Any requirement reinterpretation must retain the complete requested behavior.

## Testing Decisions

- Test public behavior at existing authorization, promotion, evaluation, graph execution, memory, telemetry, and CLI seams.
- Add regression tests for each reported failure and each new operator behavior. Prefer existing fixtures and deterministic synthetic evidence; no external target calls are required.
- Preserve existing golden regression tests and fixtures; golden dataset expansion and judge parsing are externally owned.
- Run focused tests and type checks per implementation batch, then the full offline suite, Ruff, mypy, file-size audit, and wiki lint.
- Review standards and spec conformance independently against the intake baseline.
- Baseline environment: Python 3.12, project dev dependencies. Baseline results: 714 passed, 3 skipped, two CLI wrapping assertions; both pass when rerun with COLUMNS=240 and REDTHREAD_DRY_RUN=true. Final suite uses this fixed environment.

## Out of Scope

User excluded issues #80, #89, #83, #86, #90, #93, #84, #77, #81, #87 on 2026-09-18 because another contributor is implementing them. Do not implement those fixes, including indirect duplicates. Remaining scope: #19, #75, #76, #78, #79, #82, #85, #88, #91, #92, #94. The Wave 2 map remains a tracking source, not a requirement to take over excluded work.

A GUI, rewriting LangGraph, automatic guardrail activation, universal safety certification, or live testing of third-party systems without an explicit target request.

## Further Notes

- Authoritative issue snapshot: [open issues at intake](sources/open-issues-2026-09-18.json).
- Source map: [Wave 2](https://github.com/matheusht/redthread/issues/74), plus [launch readiness](https://github.com/matheusht/redthread/issues/19).
- User explicitly requests autonomous execution; routine interview and approval steps are delegated to the orchestrator.
- GitHub access is read-only for maintainer actions; local scope and ownership records remain authoritative for this execution until remote publication succeeds.
