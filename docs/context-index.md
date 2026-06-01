# Context Index

Use this map to choose context for AI coding sessions. Default to the smallest useful set. Search before opening large docs.

## Default AI Context

- `AGENTS.md`
- `README.md`
- `docs/ai-context-summary.md`
- `docs/AGENT_DECISION_TREE.md`
- `docs/RPI_METHODOLOGY.md`

## Active Source Of Truth

- Product: `README.md`, `docs/product.md`
- Architecture and layout: `docs/TECH_STACK.md`, `docs/AGENT_ARCHITECTURE.md`
- Current phase status: `docs/PHASE_REGISTRY.md`
- Attack algorithms: `docs/algorithms.md`
- Evaluation and JudgeAgent: `docs/ANTI_HALLUCINATION_SOP.md`
- Defense synthesis and promotion: `docs/DEFENSE_PIPELINE.md`
- Evidence vocabulary: `docs/WHAT_REDTHREAD_MEANS_BY_EVIDENCE.md`
- Agentic-security runtime: `docs/AGENTIC_SECURITY_RUNTIME.md`
- Wiki system: `docs/WIKI_ARCHITECTURE.md`, `docs/WIKI_INGEST_WORKFLOW.md`, `docs/wiki/SCHEMA.md`, `docs/wiki/index.md`

## Active Research

- `docs/research/experiment-b-algorithm-benchmark/`: keep active. Research design draft for benchmarking autonomous attack strategies. Do not load by default.
- `docs/research/pyrit-adapter-deep-phases-plan.md`: PyRIT adapter plan.
- `docs/research/pyrit-defense-framework-fit-review.md`: PyRIT fit review.
- `docs/research/pyrit-text-converter-allowlist-plan.md`: converter allowlist plan.

## Load On Demand

- Phase 8 planning and testing: `docs/PRD_PHASE8_AGENTIC_SECURITY.md`, `docs/PHASE8_TESTING_GUIDE.md`
- Wiki system summaries: `docs/wiki/systems/*`
- Wiki decisions: `docs/wiki/decisions/*`
- Wiki research: `docs/wiki/research/*`
- Wiki changelog: `docs/wiki/log.md`
- Historical ledgers: compact stubs at `docs/PROGRESS.md` and `docs/REDTHREAD_STATUS_AUDIT.md`
- Autoresearch docs: `AUTORESEARCH_WALKTHROUGH.md`, `program.md`, `docs/AUTORESEARCH_PHASE3.md` through `docs/AUTORESEARCH_PHASE6.md`

## Historical Or Archived

- `docs/archive/`: reversible home for docs moved out of active context.
- `docs/archive/historical/PROGRESS.md`: full historical technical ledger.
- `docs/archive/historical/REDTHREAD_STATUS_AUDIT.md`: full 2026-04-09 historical status audit.
- `docs/archive/session-notes/`: old root-level handoff and repository-state notes.

## Do Not Inject By Default

- Large research plans.
- Changelogs.
- Historical snapshots.
- Old handoff notes.
- Ignored local files.
- Archived docs.

## Mirror Policy

`AGENTS.md` and `docs/` are authoritative. `.codex/` is the Codex-facing mirror. `.agent/` is the Antigravity-facing mirror. When changing shared behavior:

1. Update the source-of-truth doc first.
2. Update both mirrors when the behavior applies to both tools.
3. If a mirror intentionally differs, write the reason in that mirror file.
4. Do not let `.agent/` and `.codex/` silently drift on RPI, context budget, code conventions, or skill procedures.

## Review Needed

- Decide whether `docs/research/phase8_plans/` should enter git or be folded into current Phase 8 docs.
- Reconcile `.agent/` and `.codex/` mirrors in a focused follow-up pass.
