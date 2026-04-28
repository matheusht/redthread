# Wiki Index

This is the primary content map for the RedThread wiki.

## Systems

- [systems/knowledge-stack.md](systems/knowledge-stack.md) — How MemPalace, raw sources, and the wiki fit together.
- [systems/evaluation-and-anti-hallucination.md](systems/evaluation-and-anti-hallucination.md) — Evaluation baseline, grounded generation rules, and why anti-hallucination is treated as an engineering control.
- [systems/telemetry-and-monitoring.md](systems/telemetry-and-monitoring.md) — Drift detection, ASI, monitoring daemon behavior, and the signal-vs-proof boundary.
- [systems/promotion-and-revalidation.md](systems/promotion-and-revalidation.md) — Promotion discipline, revalidation evidence, and why mutation execution is kept separate from acceptance.
- [systems/defense-synthesis-and-validation.md](systems/defense-synthesis-and-validation.md) — Self-healing path from confirmed jailbreak to validated defense proposal.
- [systems/orchestration-and-engine-runtime.md](systems/orchestration-and-engine-runtime.md) — Engine facade, LangGraph supervisor flow, runtime modes, and degraded-runtime truth.
- [systems/agentic-security-runtime.md](systems/agentic-security-runtime.md) — How Phase 8 agentic-security review now plugs into the normal campaign runtime and operator artifacts.
- [systems/subsystem-focus-map.md](systems/subsystem-focus-map.md) — Current subsystem-by-subsystem focus map for what to harden now and what to delay.

## Decisions

- [decisions/adopt-mempalace-plus-llm-wiki.md](decisions/adopt-mempalace-plus-llm-wiki.md) — Why RedThread uses MemPalace for retrieval and a markdown wiki for synthesis.
- [decisions/jailbreak-benchmark-material-vault.md](decisions/jailbreak-benchmark-material-vault.md) — Why raw jailbreak benchmark material lives outside git behind reviewed manifests, hashes, approved-target gates, metadata-only run hints, and prompt-safe regression handoff artifacts.

## Entities

- [entities/README.md](entities/README.md) — Index rules and scope for entity pages.
- [entities/eni-writer-persona.md](entities/eni-writer-persona.md) — Jailbreak persona utilizing limerence, chain-of-thought hijacking, and active rebuttal.
- [entities/mempalace.md](entities/mempalace.md) — Memory and retrieval layer used by the repo.
- [entities/judge-agent.md](entities/judge-agent.md) — Evaluation role responsible for scoring attack traces.
- [entities/defense-architect.md](entities/defense-architect.md) — Grounded defensive generation role in the self-healing loop.
- [entities/open-agent-passport.md](entities/open-agent-passport.md) — Open specification for deterministic tool call authorization.
- [entities/asi.md](entities/asi.md) — Composite Agent Stability Index and what it does versus what it does not prove.

- [entities/prometheus-2.md](entities/prometheus-2.md) — Evaluation model referenced in the grounded judging stack.
- [entities/langgraph-supervisor.md](entities/langgraph-supervisor.md) — Coordinator role for macro-workflow orchestration.

## Concepts

- [concepts/README.md](concepts/README.md) — Index rules and scope for concept pages.
- [concepts/peeling-onions.md](concepts/peeling-onions.md) — Jailbreak framework using plain language, distraction, and narrative embedding.
- [concepts/confused-deputy-llm.md](concepts/confused-deputy-llm.md) — Privilege escalation in multi-agent systems via indirect prompt injection.
- [concepts/pre-action-authorization.md](concepts/pre-action-authorization.md) — Deterministic, policy-based enforcement before LLM tool call execution.
- [concepts/agentic-attack-trees-operational.md](concepts/agentic-attack-trees-operational.md) — Agentic AI Attack Trees and Operational Controls Mapping.
- [concepts/ai-security-frameworks.md](concepts/ai-security-frameworks.md) — External frameworks relevant to AI security and RedThread threat modeling.
- [concepts/ai-red-teaming-tooling-landscape.md](concepts/ai-red-teaming-tooling-landscape.md) — Survey of the AI red teaming tooling ecosystem.

## Research

- [research/README.md](research/README.md) — How to structure ongoing investigations.
- [research/ai-red-teaming-academic-papers.md](research/ai-red-teaming-academic-papers.md) — Curated bibliography of must-read academic papers on AI Red Teaming.
- [research/open-source-redteam-tool-integration-strategy.md](research/open-source-redteam-tool-integration-strategy.md) — Strategy for using garak, promptfoo, and Strix as RedThread surface expanders without replacing the closed-loop defense engine.
- [research/ai-red-teaming-guide-redthread-use-case-map.md](research/ai-red-teaming-guide-redthread-use-case-map.md) — Deep use-case map from AI-Red-Teaming-Guide and related tools into exact RedThread workflow entrypoints, infrastructure changes, and anti-overkill boundaries.
- [research/spiritual-spell-red-teaming-corpus.md](research/spiritual-spell-red-teaming-corpus.md) — Safe taxonomy and RedThread integration recommendation for the Spiritual-Spell-Red-Teaming jailbreak corpus.
- [research/spiritual-spell-red-teaming-source-inventory.md](research/spiritual-spell-red-teaming-source-inventory.md) — Metadata-only source-path inventory for the Spiritual-Spell-Red-Teaming corpus.
- [research/spiritual-spell-red-teaming-implementation-plan.md](research/spiritual-spell-red-teaming-implementation-plan.md) — Bounded implementation plan for turning the Spiritual-Spell-Red-Teaming corpus into a safe RedThread benchmark and workflow lane.
- [research/tool-technology-incorporation-assessment.md](research/tool-technology-incorporation-assessment.md) — Honest assessment of which external AI red-teaming tool ideas RedThread should absorb natively versus keep external.
- [research/tool-technology-incorporation-roadmap.md](research/tool-technology-incorporation-roadmap.md) — Detailed next-step roadmap for implementing RedThread-native plugin, strategy, detector-hint, scope, regression, and reporting concepts.
- [research/tool-technology-slice-1-implementation-plan.md](research/tool-technology-slice-1-implementation-plan.md) — Exact Slice 1 implementation checklist for RedThread-native contracts, registries, built-ins, tests, and no execution wiring.
- [research/tool-technology-slice-2-implementation-plan.md](research/tool-technology-slice-2-implementation-plan.md) — Exact Slice 2 implementation checklist for campaign planning config parsing, custom policies, scope parsing, deterministic summaries, and no execution wiring.
- [research/tool-technology-slice-3-implementation-plan.md](research/tool-technology-slice-3-implementation-plan.md) — Exact Slice 3 implementation checklist for one static seed replay strategy adapter, plugin/strategy trace lineage, scope checks, and fake-target smoke tests.
- [research/tool-technology-slice-4-implementation-plan.md](research/tool-technology-slice-4-implementation-plan.md) — Exact Slice 4 implementation checklist for garak-style weak detector hints, trace metadata attachment, JudgeAgent context inclusion, and signal-not-verdict tests.
- [research/tool-technology-slice-5-implementation-plan.md](research/tool-technology-slice-5-implementation-plan.md) — Exact Slice 5 implementation checklist for JudgeAgent-confirmed finding to RegressionCase conversion, minimized replay artifacts, dry-run validation, and finding-to-regression links.
- [research/tool-technology-slice-6-implementation-plan.md](research/tool-technology-slice-6-implementation-plan.md) — Exact Slice 6 implementation checklist for guide-style operator artifacts, Markdown/JSON exporters, detector no-overclaim wording, and regression-link report visibility.
- [research/tool-technology-slice-7-implementation-plan.md](research/tool-technology-slice-7-implementation-plan.md) — Exact Slice 7 implementation checklist for report persistence, manifest files, transcript report links, and import/export bridge prep.
- [research/tool-technology-slice-8-implementation-plan.md](research/tool-technology-slice-8-implementation-plan.md) — Exact Slice 8 implementation checklist for weak external evidence bridge models and safe promptfoo/garak/Strix mapping helpers.
- [research/tool-technology-slice-9-implementation-plan.md](research/tool-technology-slice-9-implementation-plan.md) — Exact Slice 9 implementation checklist for importing external JSON rows into RedThread weak evidence bundles.
- [research/tool-technology-slice-10-implementation-plan.md](research/tool-technology-slice-10-implementation-plan.md) — Exact Slice 10 implementation checklist for turning weak external evidence into candidate campaign/probe-seed artifacts.
- [research/tool-technology-slice-11-persona-prompting-layer-profiles.md](research/tool-technology-slice-11-persona-prompting-layer-profiles.md) — Exact Slice 11 plan and RPI findings for metadata-only persona prompting layer profiles.
- [research/tool-technology-slice-12-persona-quality-measurement.md](research/tool-technology-slice-12-persona-quality-measurement.md) — Exact Slice 12 plan and RPI findings for persona strategy coverage measurement.
- [research/tool-technology-slice-13-persona-strategy-coverage-repair.md](research/tool-technology-slice-13-persona-strategy-coverage-repair.md) — Exact Slice 13 plan and RPI findings for deterministic persona strategy coverage repair.
- [research/tool-technology-slice-14-persona-batch-layer-planning.md](research/tool-technology-slice-14-persona-batch-layer-planning.md) — Exact Slice 14 plan and RPI findings for distributing prompting layers across persona batches.
- [research/tool-technology-testing-commands-and-takeaways.md](research/tool-technology-testing-commands-and-takeaways.md) — Durable test commands, dry-run smoke analysis, and key takeaways for the Tool Technology Incorporation track.
- [research/bounded-autoresearch.md](research/bounded-autoresearch.md) — Current synthesis of bounded offense and defense mutation lanes.
- [research/current-hardening-tracks.md](research/current-hardening-tracks.md) — Current ordered execution plans for verification, governance, runtime truth, and defense confidence hardening.
- [research/next-deep-dive-subsystem.md](research/next-deep-dive-subsystem.md) — Recommendation for the next subsystem RedThread should investigate deeply after the current hardening tranche.
- [research/evaluation-truth-hardening-plan.md](research/evaluation-truth-hardening-plan.md) — Research-backed execution plan for the judge and evaluation deep dive.
- [research/defense-confidence-hardening-plan.md](research/defense-confidence-hardening-plan.md) — Research-backed execution plan for the defense synthesis, validation, and promotion deep dive.
- [research/defense-promotion-trust-pass.md](research/defense-promotion-trust-pass.md) — Durable deep-dive synthesis for what defense validation and promotion actually prove, what they do not prove, and what to harden next.
- [research/orchestration-runtime-hardening-pass.md](research/orchestration-runtime-hardening-pass.md) — Execution log for runtime-truth hardening across the engine facade, supervisor flow, and operator surfaces.
- [research/live-execution-truth-deep-dive.md](research/live-execution-truth-deep-dive.md) — Seam map, risk map, evidence map, and exact hardening slices for the real provider/runtime truth boundary.
- [research/agentic-security-shift-2025-2026.md](research/agentic-security-shift-2025-2026.md) — Research synthesis on the move from chatbot jailbreaks to tool hijacking, confused deputy chains, token exhaustion, and deterministic defenses.
- [research/atp-tennis-live-workflow-test.md](research/atp-tennis-live-workflow-test.md) — Results and interpretation of the live workflow replay pipeline against the ATP Tennis Bot using ZAPI HAR ingestion.
- [research/narrative-protocol-evolution.md](research/narrative-protocol-evolution.md) — Investigation into a first-class narrative adaptation layer for Crescendo; MVP (NarrativeState + NarrativeAdaptationPolicy) shipped as a bounded Crescendo enhancement.
- [research/stateful-workflow-replay-roadmap.md](research/stateful-workflow-replay-roadmap.md) — Concrete next-phase roadmap for evolving bounded stateful workflow replay into a more assisted, partially-autonomous system, now including shipped Phase D streaming-awareness notes, Phase E1 binding-history recording, the bounded E2 review loop, runtime-row planned/applied binding evidence, gate/runtime binding application summaries, and RedThread's passive generic `bridge_workflow_context` seam.
- [research/redthread-adoptai-strategy.md](research/redthread-adoptai-strategy.md) — Strategy page for keeping RedThread standalone while using Adopt AI in a separate integration repo, now covering HAR-derived ZAPI intake, first NoUI MCP intake, bounded live replay/workflow lanes, richer session-aware workflow context contracts and summaries, bounded response-binding carry-forward, reviewed binding override flow, bounded path/body binding targets, narrow reviewed body-field inference, operator workflow failure-class summaries, unified workflow review manifest export, streaming endpoint awareness, append-only binding-history recording, proposal-only binding-pattern candidates, reviewed alias artifacts, reviewed-alias visibility, runtime-row planned/applied binding evidence, passive generic RedThread workflow context, operator-readable gate notes, top-level bridge summary surfacing, evidence-aware gate mapping, and real RedThread replay/dry-run handoff seams.

## Timelines

- [timelines/README.md](timelines/README.md) — How to track history and roadmap evolution.
- [timelines/redthread-phase-evolution.md](timelines/redthread-phase-evolution.md) — High-level project evolution from PAIR foundation to bounded autoresearch.

## Workflow Docs

- [../WIKI_INGEST_WORKFLOW.md](../WIKI_INGEST_WORKFLOW.md) — Repeatable ingest procedure for source → wiki → index/log → lint → re-mine.
- [../WIKI_QUERY_TO_PAGE_WORKFLOW.md](../WIKI_QUERY_TO_PAGE_WORKFLOW.md) — Repeatable procedure for turning a strong chat answer into a durable wiki page.
- [../WIKI_MAINTENANCE_CHECKLIST.md](../WIKI_MAINTENANCE_CHECKLIST.md) — Daily operational checklist for safe wiki maintenance.

## Log

- [log.md](log.md) — Append-only history of wiki maintenance activity.
