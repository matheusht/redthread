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

## Entities

- [entities/README.md](entities/README.md) — Index rules and scope for entity pages.
- [entities/mempalace.md](entities/mempalace.md) — Memory and retrieval layer used by the repo.
- [entities/judge-agent.md](entities/judge-agent.md) — Evaluation role responsible for scoring attack traces.
- [entities/defense-architect.md](entities/defense-architect.md) — Grounded defensive generation role in the self-healing loop.
- [entities/open-agent-passport.md](entities/open-agent-passport.md) — Open specification for deterministic tool call authorization.
- [entities/asi.md](entities/asi.md) — Composite Agent Stability Index and what it does versus what it does not prove.

- [entities/prometheus-2.md](entities/prometheus-2.md) — Evaluation model referenced in the grounded judging stack.
- [entities/langgraph-supervisor.md](entities/langgraph-supervisor.md) — Coordinator role for macro-workflow orchestration.

## Concepts

- [concepts/README.md](concepts/README.md) — Index rules and scope for concept pages.
- [concepts/confused-deputy-llm.md](concepts/confused-deputy-llm.md) — Privilege escalation in multi-agent systems via indirect prompt injection.
- [concepts/pre-action-authorization.md](concepts/pre-action-authorization.md) — Deterministic, policy-based enforcement before LLM tool call execution.

## Research

- [research/README.md](research/README.md) — How to structure ongoing investigations.
- [research/bounded-autoresearch.md](research/bounded-autoresearch.md) — Current synthesis of bounded offense and defense mutation lanes.
- [research/current-hardening-tracks.md](research/current-hardening-tracks.md) — Current ordered execution plans for verification, governance, runtime truth, and defense confidence hardening.
- [research/next-deep-dive-subsystem.md](research/next-deep-dive-subsystem.md) — Recommendation for the next subsystem RedThread should investigate deeply after the current hardening tranche.
- [research/evaluation-truth-hardening-plan.md](research/evaluation-truth-hardening-plan.md) — Research-backed execution plan for the judge and evaluation deep dive.
- [research/defense-confidence-hardening-plan.md](research/defense-confidence-hardening-plan.md) — Research-backed execution plan for the defense synthesis, validation, and promotion deep dive.
- [research/defense-promotion-trust-pass.md](research/defense-promotion-trust-pass.md) — Durable deep-dive synthesis for what defense validation and promotion actually prove, what they do not prove, and what to harden next.
- [research/orchestration-runtime-hardening-pass.md](research/orchestration-runtime-hardening-pass.md) — Execution log for runtime-truth hardening across the engine facade, supervisor flow, and operator surfaces.
- [research/live-execution-truth-deep-dive.md](research/live-execution-truth-deep-dive.md) — Seam map, risk map, evidence map, and exact hardening slices for the real provider/runtime truth boundary.
- [research/agentic-security-shift-2025-2026.md](research/agentic-security-shift-2025-2026.md) — Research synthesis on the move from chatbot jailbreaks to tool hijacking, confused deputy chains, token exhaustion, and deterministic defenses.
- [research/redthread-adoptai-strategy.md](research/redthread-adoptai-strategy.md) — Strategy page for keeping RedThread standalone while using Adopt AI in a separate integration repo, now covering HAR-derived ZAPI intake, first NoUI MCP intake, bounded live replay/workflow lanes, richer session-aware workflow context contracts and summaries, bounded response-binding carry-forward, first bridge-emitted query-binding hints, reviewed binding override flow, bounded path/body binding targets, narrow reviewed body-field inference, richer operator workflow failure-class summaries, unified workflow review manifest export, operator-readable gate notes, top-level bridge summary surfacing, evidence-aware gate mapping, and real RedThread replay/dry-run handoff seams.

## Timelines

- [timelines/README.md](timelines/README.md) — How to track history and roadmap evolution.
- [timelines/redthread-phase-evolution.md](timelines/redthread-phase-evolution.md) — High-level project evolution from PAIR foundation to bounded autoresearch.

## Workflow Docs

- [../WIKI_INGEST_WORKFLOW.md](../WIKI_INGEST_WORKFLOW.md) — Repeatable ingest procedure for source → wiki → index/log → lint → re-mine.
- [../WIKI_QUERY_TO_PAGE_WORKFLOW.md](../WIKI_QUERY_TO_PAGE_WORKFLOW.md) — Repeatable procedure for turning a strong chat answer into a durable wiki page.
- [../WIKI_MAINTENANCE_CHECKLIST.md](../WIKI_MAINTENANCE_CHECKLIST.md) — Daily operational checklist for safe wiki maintenance.

## Log

- [log.md](log.md) — Append-only history of wiki maintenance activity.
