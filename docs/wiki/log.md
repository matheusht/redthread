# Wiki Log

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
