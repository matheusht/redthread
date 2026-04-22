# Wiki Log

## [2026-04-22] stateful-workflow-replay-phase-e1 | implemented binding outcome history recording
- updated `docs/wiki/research/stateful-workflow-replay-roadmap.md` to mark Phase E1 as shipped in `adopt-redthread`
- updated `docs/wiki/research/redthread-adoptai-strategy.md` to record the new append-only `binding_history.jsonl` artifact for successful applied bindings
- updated `docs/wiki/index.md` so future sessions can find the E1 history-recording seam quickly

## [2026-04-22] stateful-workflow-replay-phase-d | implemented Phase D streaming endpoint awareness
- updated `docs/wiki/research/stateful-workflow-replay-roadmap.md` to mark Phase D1 and D2 as shipped in `adopt-redthread`
- updated `docs/wiki/research/redthread-adoptai-strategy.md` to record the new bounded streaming behavior: first-chunk evidence, `stream_open_partial_read`, and configurable `stream_max_bytes`
- updated `docs/wiki/research/atp-tennis-live-workflow-test.md` with the follow-up note that the ATP timeout result was the precursor to the new bounded streaming lane
- updated `docs/wiki/index.md` so future sessions can find the Phase D streaming-awareness state quickly

## [2026-04-22] stateful-workflow-replay-phase-c | implemented Phase C operator manifest-first flow
- strengthened `workflow_review_manifest.json` in `adopt-redthread` so it now surfaces top-level and per-workflow `required_contexts`, `body_template_gaps`, and `open_questions` for pre-run operator review
- bridge workflow now writes the manifest before live workflow replay and refreshes it after replay with enriched candidate/body/path/header review data when live results exist
- added plain-English workflow failure narratives in replay output: per-workflow `failure_narrative`, top-level `workflow_failure_narratives`, and per-step `workflow_evidence.result_narrative`
- split manifest support into smaller helper modules to stay inside repo file-size guidance and added focused Phase C tests; Phase A/B regression tests still pass

## [2026-04-22] stateful-workflow-replay-phase-b | implemented Phase B session continuity detection
- created `adapters/bridge/session_continuity.py` (Phase B1+B2): `parse_set_cookie_names()` / `parse_all_set_cookie_names()` parse Set-Cookie headers; `detect_candidate_header_bindings()` walks ordered workflow steps, matches set-cookie response → downstream cookie request header, emits `exact_name_match` candidates or `unmatched` when no downstream user; `session_continuity_note()` formats human-readable B2 contract string
- extended `adapters/bridge/workflow_review_manifest.py`: manifest workflows now carry `candidate_header_binding_pairs` (empty at plan time, populated after enrich) and `session_continuity_note`; `_discover_header_binding_pairs()` provides structural skeleton; `enrich_manifest_candidates()` now accepts optional `cases` dict and runs B1 detection with real response headers post-replay; `_candidate_summary` counts all candidate types (body + path + header)
- added `tests/test_session_continuity.py`: 29 tests covering cookie parsing, B1 detection (matched/unmatched/multi-cookie/header_names), B2 note formatting, manifest integration at plan-time and post-replay, the no-mutation invariant, and the safety invariant (header candidates never in response_bindings)
- all 29 new tests pass; 38 Phase A tests still pass; zero regressions to 46 pre-existing green tests (113 total)

## [2026-04-22] stateful-workflow-replay-phase-a | implemented Phase A candidate dependency discovery
- created `adapters/bridge/binding_alias_table.py` with the curated alias table (Phase A2): 12 manually-seeded source→target mappings, `alias_lookup()` returning (target_path, tier) tuples with exact_name_match → alias_match → heuristic_match priority
- added `discover_candidate_bindings()` to `adapters/bridge/workflow_binding_inference.py` (Phase A1): walks response JSON scalar paths from step N, runs alias_lookup on each, emits tiered candidate bindings for step N+1 body/URL — proposals only, never applied
- added `discover_candidate_path_bindings()` to `adapters/bridge/workflow_binding_inference.py` (Phase A3): extracts {placeholder} slots from URL templates at step N+1, matches via alias table, emits unmatched entries when no live response JSON is available (plan-time structural discovery)
- added `_flatten_json_paths()` helper: recursively flattens response JSON to dot-path scalar tuples, skips lists
- updated `adapters/bridge/workflow_review_manifest.py`: manifest now carries `candidate_binding_summary` (tier counts), `candidate_binding_pairs` per workflow (A1+A3 pairs per step pair), and `enrich_manifest_candidates()` for post-replay enrichment with real response JSON
- added `tests/test_candidate_binding_discovery.py`: 38 tests covering alias table round-trips, A1 exact/alias/heuristic matching, A3 path slot extraction and unmatched handling, manifest integration, enrichment correctness, and the invariant that candidates never appear in response_bindings
- all 38 new tests pass; zero regressions to the 46 pre-existing green tests

## [2026-04-22] stateful-workflow-replay-roadmap | written next-phase roadmap from ATP Tennis Bot lessons

- created `docs/wiki/research/stateful-workflow-replay-roadmap.md` to translate the ATP test into a concrete, ordered 5-phase roadmap
- phases cover: candidate dependency discovery, session continuity detection, manifest-first operator flow, streaming endpoint awareness, and bounded pattern learning
- each phase has explicit human vs machine responsibility boundaries to prevent autonomy creep
- explicitly documents what stays out of scope: CSRF, full cookie jar, branching workflows, nested schema inference, auto-retry
- registered in `docs/wiki/index.md`


- updated `docs/wiki/research/atp-tennis-live-workflow-test.md` to document the final successful pipeline run against the ATP Tennis Bot
- upgraded `adopt-redthread` core engine to support `request_header` binding targets natively in `adapters/live_replay/workflow_bindings.py`
- implemented dynamic fallback body injection for HAR ingestors that strip request bodies for privacy
- proved the engine can dynamically map session cookies and payload IDs between steps, resolving Vercel AI SDK 404/400 validation errors
- successfully caught and documented streaming LLM inference timeouts (`TimeoutError`) as valid execution artifacts without crashing the engine

## [2026-04-22] atp-tennis-bot-live-test | executed live workflow replay with auth and write context
- documented the ATP Tennis Bot testing results in `docs/wiki/research/atp-tennis-live-workflow-test.md`
- confirmed that the pipeline securely halts at the review gate when auth/write context is missing
- proved that live workflow replay successfully carries session state forward and aborts gracefully on HTTP 400 errors (contract mismatches)
- highlighted the necessity of Binding Overrides for dynamic IDs (like `chatId`) across grouped workflow steps
## [2026-04-22] adopt-bridge-review-manifest-pass | recorded unified workflow review manifest
- updated `docs/wiki/research/redthread-adoptai-strategy.md` to capture the next bounded bridge step: `adopt-redthread` now writes a unified `workflow_review_manifest.json` that combines workflow/session context requirements, response-binding review decisions, replay status, and failure summaries for operator review
- kept the boundary honest: this is a review/export convenience artifact only, not browser orchestration, session repair, or new live execution power inside RedThread core
- updated `docs/wiki/index.md` so future sessions can find the operator review manifest seam quickly

## [2026-04-22] adopt-bridge-workflow-summary-pass | recorded richer operator workflow contract summaries
- updated `docs/wiki/research/redthread-adoptai-strategy.md` to capture the bounded Phase 9.5 follow-through: `adopt-redthread` now surfaces explicit same-auth/same-write workflow contract fields plus workflow failure-class summaries in replay, bridge summary, and gate-visible notes
- kept the boundary honest: this is operator-facing contract visibility only, not browser orchestration, session repair, or a broader live automation claim inside RedThread core
- updated `docs/wiki/index.md` so future sessions can find the workflow-summary seam quickly

## [2026-04-22] adopt-bridge-body-inference-pass | recorded narrow reviewed body-field inference
- updated `docs/wiki/research/redthread-adoptai-strategy.md` to capture Phase 9.4: `adopt-redthread` now emits a narrow automatic body-field inference class for id-like JSON body fields using the immediately previous step response JSON by exact field name, while still requiring pending-review approval and explicit reviewed-write opt-in before live execution
- kept the architecture split explicit: this is still bounded reviewed binding control inside the Adopt bridge, not broad schema inference, browser orchestration, session repair, or freeform mutation inside RedThread core
- updated `docs/wiki/index.md` so future sessions can find the narrow body-inference seam quickly

## [2026-04-22] adopt-bridge-path-binding-pass | recorded bounded path binding and review artifacts
- updated `docs/wiki/research/redthread-adoptai-strategy.md` to capture Phase 9.3: `adopt-redthread` now supports bounded `request_path` binding targets, surfaces inferred/approved/pending/rejected/replaced binding counts, and emits per-workflow binding review artifacts so operators can inspect review decisions directly in replay output
- kept the architecture split explicit: this is still bounded reviewed binding control inside the Adopt bridge, not broad path/body inference, browser orchestration, session repair, or freeform mutation inside RedThread core
- updated `docs/wiki/index.md` so future sessions can find the new path-binding and review-artifact seam quickly

## [2026-04-22] adopt-bridge-binding-review-pass | recorded reviewed binding inference pack
- updated `docs/wiki/research/redthread-adoptai-strategy.md` to capture Phase 9.2: inferred workflow bindings now carry explicit review metadata, replay blocks pending-review inferred bindings with `binding_review_required`, the bridge pipeline can accept a binding override file, and reviewed write flows can use bounded `request_body_json` binding when write approval explicitly opts in
- kept the architecture split explicit: this is still bounded reviewed binding control inside the Adopt bridge, not browser orchestration, session repair, or freeform mutation inside RedThread core
- updated `docs/wiki/index.md` so future sessions can find the reviewed binding override seam quickly

## [2026-04-22] adopt-bridge-auto-binding-hint-pass | recorded first bridge-emitted binding hints
- updated `docs/wiki/research/redthread-adoptai-strategy.md` to capture the next bounded bridge step: `adopt-redthread` now preserves full captured request URLs and can automatically emit a narrow class of response bindings for later id-like query parameters in workflow steps, instead of requiring hand-edited workflow JSON for every binding case
- kept the architecture split explicit: this is still a narrow bridge heuristic and not full body/path inference, browser orchestration, or session repair
- updated `docs/wiki/index.md` so future sessions can find the first auto-binding seam quickly

## [2026-04-22] adopt-bridge-response-binding-pass | recorded bounded response-derived carry-forward
- updated `docs/wiki/research/redthread-adoptai-strategy.md` to capture the next bounded bridge step: `adopt-redthread` now supports declared response bindings from prior step JSON/headers into later request URL placeholders, emits extracted/applied binding evidence, and surfaces binding counts plus binding-mismatch reasons in workflow summaries and gate-facing output
- kept the architecture split explicit: this is still bounded declared value carry-forward in the Adopt bridge, not browser orchestration, session repair, or freeform request mutation inside RedThread core
- updated `docs/wiki/index.md` so future sessions can find the new bounded response-binding seam quickly

## [2026-04-22] adopt-bridge-workflow-operator-summary-pass | recorded operator-visible workflow contract summaries
- updated `docs/wiki/research/redthread-adoptai-strategy.md` to capture the next bounded bridge step: `adopt-redthread` now surfaces workflow requirement summaries in top bridge artifacts and gate notes, and now detects bounded `auth_header_family_mismatch` failures when approved auth context does not match captured auth header requirements
- kept the architecture split explicit: this is still bounded contract validation and evidence surfacing, not browser orchestration or session repair
- updated `docs/wiki/index.md` so future sessions can find the operator-visible workflow summary change quickly

## [2026-04-22] adopt-bridge-workflow-context-summary-pass | recorded richer bounded workflow contracts and summaries
- updated `docs/wiki/research/redthread-adoptai-strategy.md` to capture the Phase 8.1 bridge state: `adopt-redthread` now adds same-target-env continuity, required header-family hints, explicit predecessor-step dependency contracts, and machine-readable workflow requirement summaries on top of the earlier bounded workflow-context layer
- kept the architecture split explicit: Adopt tools still provide discovery/runtime realism, `adopt-redthread` still adapts artifacts and bounded live workflow controls, and RedThread still remains the attack/replay/validation/hardening engine rather than a browser automation runtime
- updated `docs/wiki/index.md` so future sessions can find the stronger workflow-contract + summary framing quickly

## [2026-04-22] adopt-bridge-workflow-context-pass | recorded bounded session-aware workflow context packs
- updated `docs/wiki/research/redthread-adoptai-strategy.md` to capture the new bridge state: `adopt-redthread` now declares bounded workflow/session context requirements, validates approved auth or write context before workflow replay, and surfaces clearer gate-facing reasons for review gaps versus context mismatch
- kept the architecture split explicit: Adopt tools still provide discovery/runtime realism, `adopt-redthread` still adapts artifacts and bounded live workflow controls, and RedThread still remains the attack/replay/validation/hardening engine rather than a browser automation runtime
- updated `docs/wiki/index.md` so future sessions can find the stronger session-aware workflow-context framing quickly

## [2026-04-22] adopt-bridge-workflow-evidence-pass | recorded bounded workflow evidence and gate mapping
- updated `docs/wiki/research/redthread-adoptai-strategy.md` to capture the new bridge state: `adopt-redthread` now carries bounded workflow evidence forward across grouped live workflow replay, emits structured workflow failure reasons, and feeds those results into the evidence-aware replay gate
- kept the architecture split explicit: Adopt tools still provide discovery/runtime realism, `adopt-redthread` still adapts artifacts and bounded live evidence, and RedThread still remains the attack/replay/validation/hardening engine rather than a browser automation runtime
- updated `docs/wiki/index.md` so future sessions can find the stronger bounded workflow-evidence + gate-mapping framing quickly

## [2026-04-21] adopt-bridge-live-runner-pass | recorded one-command live bridge workflow
- updated `docs/wiki/research/redthread-adoptai-strategy.md` to capture the new bridge state: `adopt-redthread` now has a one-command artifact pipeline, a one-command live ZAPI capture runner, replay-plan/gate generation from the same normalized fixture contract, and the same RedThread replay/dry-run handoff seams
- kept the architecture split explicit: Adopt tools still provide app-specific discovery/runtime surfaces, `adopt-redthread` still adapts those artifacts, and RedThread still remains the attack/replay/validation/hardening engine
- updated `docs/wiki/index.md` so future sessions can find the strategy page using the stronger live-runner + workflow-automation framing

## [2026-04-20] adopt-bridge-runtime-and-noui-pass | recorded runtime handoff seam and NoUI intake
- updated `docs/wiki/research/redthread-adoptai-strategy.md` to capture the new bridge state: `adopt-redthread` now supports HAR-derived ZAPI intake, first NoUI MCP server intake, RedThread replay-bundle export, promotion-gate evaluation, and dry-run campaign-case execution
- kept the architecture split explicit: Adopt tools provide app-specific discovery/runtime surfaces, `adopt-redthread` adapts those artifacts, and RedThread remains the attack/replay/validation/hardening engine
- updated `docs/wiki/index.md` so future sessions can find the strategy page using the stronger runtime-handoff + NoUI framing

## [2026-04-20] adopt-bridge-har-pass | recorded real HAR intake without RedThread core drift
- updated `docs/wiki/research/redthread-adoptai-strategy.md` with the new bridge milestone: `adopt-redthread` now supports a HAR-derived ZAPI intake lane that filters noisy browser traffic into RedThread-friendly fixtures
- kept the architecture boundary explicit: Adopt tools improve discovery and app-specific surface generation, `adopt-redthread` adapts artifacts, and RedThread remains the attack/replay/validation/hardening engine
- updated `docs/wiki/index.md` so future sessions can find the strategy page with the new HAR-intake framing quickly

## [2026-04-20] adopt-strategy-pass | added standalone-vs-integration strategy page
- added `docs/wiki/research/redthread-adoptai-strategy.md` to capture the recommended split: keep RedThread standalone and move Adopt AI integration work into a separate repo
- recorded role boundaries for Adopt AI as the builder plane and RedThread as the security assurance plane
- documented phased ZAPI workflow levels from discovery-only intake through pre-publish certification
- updated `docs/wiki/index.md` so the new strategy page is discoverable

## [2026-04-18] live-execution-truth-pass-m4 | finished interception, attack-lane labeling, and smoke coverage
- added a common-boundary interception hook under `src/redthread/pyrit_adapters/interceptors.py` so instrumented live sends can be blocked before provider execution
- wired the first mainstream blocked path through persona generation using shared authorization metadata and a new interception test
- added attack-lane seam labels across PAIR, TAP, Crescendo, and MCTS so the execution-truth summary now sees core offensive runtime traffic too
- added `tests/test_live_execution_truth_smoke.py` as the tiny opt-in smoke-suite scaffold for live persona, target, judge, telemetry, and blocked-send proof
- updated the live execution truth research page and orchestration runtime system page to mark the planned pass complete

## [2026-04-18] live-execution-truth-pass-m3 | added campaign-level execution truth aggregation
- added a context-scoped execution recorder so instrumented live sends can be collected across one campaign without threading recorder state through every worker boundary
- added execution-truth aggregation in campaign metadata and transcript summary via `execution_truth_summary` and `execution_records_sample`
- split the oversized engine facade into smaller helper modules while preserving `RedThreadEngine` behavior
- added focused regression coverage in `tests/test_execution_truth_summary.py` and extended `tests/test_runtime_truth.py` to pin the new transcript/runtime fields
- refreshed the live execution truth research page and orchestration runtime system page so the new operator-facing evidence surface is documented

## [2026-04-18] live-execution-truth-pass-m2 | instrumented persona, defense, and telemetry seams
- added shared seam labeling for `persona.generate`, `defense.architect`, `defense.replay`, `telemetry.canary`, and `telemetry.warmup`
- preserved compatibility with non-instrumented targets and test doubles by adding `send_with_execution_metadata(...)`
- split `src/redthread/personas/generator.py` and `src/redthread/core/defense_synthesis.py` support code so the new behavior stayed under the repo file-cap rule
- added focused regression coverage in `tests/test_persona_execution_records.py`, `tests/test_defense_execution_records.py`, and `tests/test_telemetry_execution_records.py`
- refreshed the live execution truth research page plus defense and telemetry system pages so the shipped seam coverage and remaining gaps stay explicit

## [2026-04-18] live-execution-truth-pass-m1 | landed shared execution records and judge seam labels
- extracted the oversized PyRIT adapter wrapper into smaller modules under `src/redthread/pyrit_adapters/` to stay inside the repo file-cap guidance
- added `src/redthread/pyrit_adapters/execution_records.py` so `RedThreadTarget.send(...)` can emit normalized execution records without breaking its old return type
- instrumented `src/redthread/evaluation/judge.py` so `judge.autocot` and `judge.score` now pass seam labels through the common target boundary
- added focused regression coverage in `tests/test_target_execution_records.py` and `tests/test_judge_execution_records.py`
- refreshed the live execution truth research page and evaluation system page so the shipped slice and remaining gaps are documented honestly

## [2026-04-17] live-execution-truth-pass | mapped the real provider/runtime boundary
- added `docs/wiki/research/live-execution-truth-deep-dive.md` with a seam map, risk map, evidence map, exact implementation slices, and recommended order of attack for the live execution truth subsystem
- grounded the page in source docs plus the current runtime, evaluation, judge, telemetry, persona, defense replay, and target-factory code paths
- recorded the main next move as building a shared execution-truth spine at `src/redthread/pyrit_adapters/targets.py` before widening interception or claiming broader live proof

## [2026-04-17] phase8-live-proof-pass | added a tiny opt-in live interception lane
- added `src/redthread/tools/authorization/live_intercept.py` with `run_live_authorization_smoke()` to prove one real local pre-action authorization boundary
- connected the same decision path to `src/redthread/pyrit_adapters/controlled.py` so `ControlledLiveAdapter.send(..., action=...)` can block a wrapped live target send before execution
- extended the same pattern to `src/redthread/tools/attack_tool.py` so an optional `ActionEnvelope` in tool context metadata can block the live target send before execution
- extended the same pattern to `src/redthread/tools/sandbox_tool.py` so an optional `ActionEnvelope` in tool context metadata can block the replay send before execution
- extended the same pattern to `src/redthread/core/defense_replay_runner.py` so each live replay case is authorized before the patched target send and the decision is stored on replay-case evidence
- added focused tests so opt-in skip, deny-no-execute, allow-executes, adapter-boundary interception, attack-tool interception, sandbox-tool interception, and defense-replay interception behavior are pinned
- refreshed `docs/AGENTIC_SECURITY_RUNTIME.md` and `docs/wiki/systems/agentic-security-runtime.md` so the new proof lane is described honestly as narrow proof-of-control, not broad production enforcement

## [2026-04-17] phase8-trust-core-pass | documented capability taxonomy and trust-core hardening
- refreshed `docs/AGENTIC_SECURITY_RUNTIME.md` with the current trust-core status: shared capability taxonomy, enum-backed trust policies, canonical trust semantics, and explicit authorization precedence
- updated `docs/wiki/systems/agentic-security-runtime.md` so the durable wiki explains what the new Phase 8 auth/provenance hardening does and what gap remains
- recorded the next honest milestone as a tiny opt-in live-proof lane instead of overstating sealed runtime review

## [2026-04-16] runtime-pass | wired phase 8 into campaign runtime and documented it
- added `docs/AGENTIC_SECURITY_RUNTIME.md` as the source doc for the new additive runtime hook
- added `docs/wiki/systems/agentic-security-runtime.md` to explain where the sealed runtime review runs and what evidence it produces
- updated `docs/wiki/index.md` so the new runtime page is discoverable

## [2026-04-16] research-pass | added agentic security shift synthesis
- added `docs/wiki/research/agentic-security-shift-2025-2026.md` covering MCP tool hijacking, confused deputy chains, token exhaustion, and deterministic defenses
- updated `docs/wiki/index.md` so the new research page is discoverable
- grounded the page in MemPalace recall plus external sources on OWASP MCP tool poisoning, MAS hijacking, Clawdrain, and OAP-style pre-action authorization

## [2026-04-13] scaffold | initialized redthread wiki
- created `docs/WIKI_ARCHITECTURE.md`
- created `docs/wiki/SCHEMA.md`
- created `docs/wiki/index.md` and `docs/wiki/log.md`
- added starter pages for systems, decisions, and page-family readmes
- connected wiki guidance to MemPalace setup and agent instructions

## [2026-04-13] content-pass | seeded first operational wiki pages
- added system pages for evaluation, telemetry, and promotion/revalidation
- added research synthesis page for bounded autoresearch
- added `docs/WIKI_INGEST_WORKFLOW.md` as the repeatable wiki ingest procedure
- added `scripts/wiki_lint.py` and `make wiki-lint` to validate wiki structure

## [2026-04-13] entity-pass | added first named wiki entities and timeline
- added entity pages for MemPalace, JudgeAgent, Defense Architect, and ASI
- added a timeline page for phase evolution
- added `docs/WIKI_QUERY_TO_PAGE_WORKFLOW.md` for answer-driven wiki growth

## [2026-04-13] expansion-pass | added maintenance checklist and more seed pages
- added `docs/WIKI_MAINTENANCE_CHECKLIST.md` for daily wiki operations
- added entity pages for Prometheus 2 and LangGraph Supervisor
- added a system page for defense synthesis and validation

## [2026-04-14] focus-pass | added current focus map and hardening tracks
- added `docs/wiki/systems/subsystem-focus-map.md` for subsystem-by-subsystem priority guidance
- added `docs/wiki/research/current-hardening-tracks.md` for ordered hardening plans across verification, governance, runtime truth, and defense confidence
- updated `docs/wiki/index.md` so the new pages are discoverable

## [2026-04-14] verification-pass | restored a green default verification baseline
- made `tests/test_golden_dataset.py` sealed/offline by default and left live golden evaluation as an explicit opt-in path
- corrected Phase 6 template drift in `src/redthread/research/defense_source_mutation_registry.py` so bounded defense mutation tests align with the current defense prompt assets
- verified the repo is currently green with `201 passed`

## [2026-04-14] hardening-pass | completed governance, runtime-truth, and defense-confidence follow-through
- documented the real governance boundary in `README.md`: the bounded research daemon pauses for manual Phase 3 review instead of auto-accepting new proposals
- sealed the campaign dry-run path by making persona generation deterministic, switching attack runtimes to lazy provider construction, and skipping telemetry during dry-run
- added explicit runtime-mode labels to campaign transcripts so operators can distinguish sealed dry-run evidence from live-provider evidence
- expanded defense replay utility coverage and enriched validation reports with counts and failure reasons for easier promotion inspection
- verified the repo is currently green with `203 passed`

## [2026-04-14] research-pass | selected the next deep-dive subsystem
- added `docs/wiki/research/next-deep-dive-subsystem.md` to record the post-hardening recommendation
- updated `docs/wiki/index.md` so the new research page is discoverable
- recommended telemetry and monitoring as the next deep investigation because it now has the best leverage-to-ambiguity ratio after the trust hardening tranche

## [2026-04-15] telemetry-truth-pass | hardened telemetry claims against runtime reality
- updated telemetry source docs to clarify the current probe-first runtime path and the limit between monitoring signal and proof
- rewrote `docs/wiki/systems/telemetry-and-monitoring.md` around what telemetry measures, what ASI/drift mean in practice, and which daemon actions are safe to automate
- refreshed `docs/wiki/entities/asi.md` and `docs/wiki/index.md` so operators can find the new trust-boundary framing quickly

## [2026-04-15] evaluation-research-pass | planned the next judge/evaluation deep dive
- researched the next subsystem after telemetry and confirmed judge/evaluation is now the highest-value truth-layer investigation
- added `docs/wiki/research/evaluation-truth-hardening-plan.md` with exact milestones, file targets, trust gaps, and acceptance criteria
- updated `docs/wiki/index.md` so the new research plan is easy to find

## [2026-04-15] evaluation-truth-pass-m1 | added explicit evaluation evidence modes
- added `src/redthread/evaluation/results.py` so evaluation outputs now carry explicit evidence mode metadata instead of raw score only
- updated `src/redthread/evaluation/pipeline.py` to distinguish `sealed_heuristic`, `live_judge`, and `live_judge_fallback` paths and to carry fallback reasons into aggregate results
- added `tests/test_evaluation_truth.py` and refreshed the evaluation wiki page so sealed CI, live judge evidence, and failure fallback are described honestly

## [2026-04-15] evaluation-truth-pass-m2 | pinned regression tests for truth boundaries
- added `tests/test_evaluation_boundaries.py` to lock mixed evidence-mode reporting and high-risk heuristic edges like prompt leakage, direct disclosure, and refusal dominance
- extended evaluation truth docs so the pinned edge cases are explicit instead of implied
- refreshed `docs/wiki/entities/judge-agent.md` so operators can see the line between live judge evidence and weaker sealed or fallback scoring

## [2026-04-15] evaluation-truth-pass-m3 | finished the honesty pass across docs and wiki
- tightened `README.md` so sealed CI, successful live judge evidence, and fallback scoring are described as different evidence strengths
- updated `docs/PROGRESS.md`, `docs/ANTI_HALLUCINATION_SOP.md`, and `docs/PHASE_REGISTRY.md` so the source docs match the real evaluation truth boundary
- refreshed `docs/wiki/entities/judge-agent.md` metadata after the evaluation honesty pass so the wiki stays aligned with the source docs

## [2026-04-15] defense-confidence-research-pass | planned the defense confidence deep dive
- added `docs/wiki/research/defense-confidence-hardening-plan.md` with milestones for defense evidence modes, replay confidence, promotion evidence, and structural cleanup
- updated `docs/wiki/index.md` so the new defense hardening plan is discoverable
- grounded the plan in source docs plus current runtime evidence from defense replay, utility gate, promotion, and report inspection paths

## [2026-04-15] defense-confidence-pass-m1 | added explicit defense evidence modes
- added explicit defense evidence classes for `sealed_dry_run_replay`, `live_replay`, and `live_validation_error`
- tightened promotion utility gating so promotability depends on strong defense evidence instead of coarse validation mode alone
- updated defense docs/wiki so operators can see what each defense evidence class proves and what it does not

## [2026-04-15] defense-confidence-pass-m2 | hardened replay suite confidence
- expanded the default replay suite to `default-defense-replay-v3` with an `exploit_override_probe` plus extra bounded benign utility cases
- pinned weak exploit-blocking and over-refusal regressions in focused replay confidence tests
- documented replay breadth honestly so operators can see what the suite covers and what it still does not prove

## [2026-04-15] defense-confidence-pass-m3 | hardened promotion evidence inspection
- added explicit promotion evidence buckets for missing reports, weak evidence, failed replay validation, and per-trace failure maps
- updated promotion failure reasons and CLI output so operators can see why promotion failed without opening raw JSON manually
- documented promotion as an evidence gate rather than a magic approval step

## [2026-04-15] defense-confidence-pass-m4 | cleaned defense hardening structure
- reduced `src/redthread/research/promotion.py` to the 200-line target by extracting checkpoint persistence
- split oversized defense and promotion tests into smaller files by concern
- moved shared defense test builders into a helper module so future hardening work carries less context and duplication

## [2026-04-15] research-note-refresh | documented the defense deep-dive selection result
- refreshed `docs/wiki/research/next-deep-dive-subsystem.md` to capture the research result that selected defense synthesis/validation plus promotion/revalidation
- recorded the selection in caveman-clear language: next hardening track in source docs, RedThread core differentiator, and trust story needed stronger evidence layers
- marked the page as a completed historical research result because the defense-confidence pass has now been executed

## [2026-04-15] defense-promotion-trust-pass-m1 | durable research synthesis for defense and promotion trust
- added `docs/wiki/research/defense-promotion-trust-pass.md` to capture the new deep-dive findings about what defense validation and promotion do and do not prove
- recorded the main trust gaps for this pass: operator bridge from promotion bucket to replay failure, bounded replay breadth, and doc overclaim risk
- linked the new research page from `docs/wiki/index.md` so future sessions can start from the durable synthesis instead of re-deriving it

## [2026-04-15] defense-promotion-trust-pass-m3 | bounded replay v4 and final closeout
- updated `docs/DEFENSE_PIPELINE.md` and `docs/wiki/systems/defense-synthesis-and-validation.md` for `default-defense-replay-v4`, including the new `exploit_roleplay_probe` and `yaml_status_note` coverage
- refreshed `docs/wiki/research/current-hardening-tracks.md` with the new operator-inspection bridge and replay-breadth execution note
- marked `docs/wiki/research/defense-promotion-trust-pass.md` complete after the wiki, operator-inspection, and replay-breadth milestones all shipped and passed verification

## [2026-04-15] orchestration-runtime-pass-m1 | added degraded runtime truth to campaign artifacts
- added `src/redthread/orchestration/runtime_summary.py` and wired supervisor runtime counts for attack, judge, and defense worker failures
- updated campaign metadata and transcript summaries so operators can see `degraded_runtime`, `error_count`, and compact runtime-stage counts
- added new wiki pages for `systems/orchestration-and-engine-runtime.md` and `research/orchestration-runtime-hardening-pass.md`, then linked them from the wiki index

## [2026-04-15] orchestration-runtime-pass-m2 | surfaced runtime truth in dashboard history
- split transcript parsing into `src/redthread/dashboard_history.py` so the dashboard module stays under the repo size target while the history parser can grow independently
- updated `src/redthread/dashboard.py` so operators can see mode, clean-vs-degraded runtime state, and compact `A/J/D` worker-failure counts
- added `tests/test_dashboard.py` to pin runtime parsing and rendered dashboard output for the new operator surface

## [2026-04-15] orchestration-runtime-pass-m3 | exposed judge passthrough truth per trace and closed the pass
- updated `src/redthread/orchestration/graphs/judge_graph.py` so traces now carry explicit `judge_runtime_status` metadata for sealed passthrough, live re-evaluation, and live judge error passthrough
- updated `src/redthread/engine.py` transcript attack-result lines to expose `judge_runtime_status` and `judge_error` for operator inspection
- marked `docs/wiki/research/orchestration-runtime-hardening-pass.md` complete and refreshed `docs/wiki/entities/langgraph-supervisor.md` with current runtime-truth notes

## [2026-04-15] evaluation-truth-pass-m1 | surfaced aggregate evaluation evidence reporting
- updated `src/redthread/evaluation/results.py` and `src/redthread/evaluation/pipeline.py` so golden evaluation now aggregates evidence counts and flags mixed-mode / degraded fallback runs
- fixed `redthread test golden` to pass `objective` into `pipeline.evaluate_trace()` and to surface evidence counts, degraded warnings, and per-trace evidence mode in the CLI output
- added focused coverage in `tests/test_evaluation_truth.py`, `tests/test_evaluation_boundaries.py`, and new `tests/test_evaluation_cli.py`; refreshed evaluation wiki pages with the shipped operator-truth slice

## [2026-04-16] research-pass | ingested agentic confused deputy and OAP research
- added concept page for `concepts/confused-deputy-llm.md` (Reddit)
- added concept page for `concepts/pre-action-authorization.md` (Arxiv)
- added entity page for `entities/open-agent-passport.md` (Arxiv)
- updated wiki index to include new research synthesis
