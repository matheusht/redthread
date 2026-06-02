# AI Context Summary

This is the compact starting context for AI coding agents. Load this before opening broad docs. It points to active sources and keeps historical research out of the default prompt.

## Load First

- `AGENTS.md`: repo agent contract, RPI rules, file-size rules, and mirror policy.
- `README.md`: product purpose, operator flow, and current public framing.
- `docs/context-index.md`: active documentation map and load-on-demand rules.
- `docs/AGENT_DECISION_TREE.md`: task-to-doc routing.
- `docs/RPI_METHODOLOGY.md`: research, plan, implement workflow.

## Current Direction

RedThread is a CLI-first AI security engine. Its product spine is:

```text
attack -> judge -> defend -> replay -> promotion evidence
```

The current direction is proof confidence, live reliability, evidence honesty, operator clarity, deterministic agentic-security validation, and careful self-healing hardening. Do not add new dashboards, hidden state machines, agents, evidence states, or auto-promotion by default.

## Active Sources Of Truth

- Product and operator truth: `README.md`, `docs/product.md`.
- Architecture and code layout: `docs/TECH_STACK.md`, `docs/AGENT_ARCHITECTURE.md`.
- Phase status and roadmap: `docs/PHASE_REGISTRY.md`.
- Attack algorithms: `docs/algorithms.md`.
- Evaluation and anti-hallucination: `docs/ANTI_HALLUCINATION_SOP.md`.
- Defense loop: `docs/DEFENSE_PIPELINE.md`.
- Evidence vocabulary: `docs/WHAT_REDTHREAD_MEANS_BY_EVIDENCE.md`.
- Agentic-security runtime: `docs/AGENTIC_SECURITY_RUNTIME.md`.
- Knowledge system: `docs/WIKI_ARCHITECTURE.md`, `docs/WIKI_INGEST_WORKFLOW.md`, `docs/wiki/index.md`.

## Active Research To Keep

- `docs/research/experiment-b-algorithm-benchmark/`: active research design for comparing autonomous attack strategies under one shared harness. Keep in git. Load only for benchmark or algorithm-comparison work.

## Load On Demand

- Phase 8 details: `docs/PRD_PHASE8_AGENTIC_SECURITY.md`, `docs/PHASE8_TESTING_GUIDE.md`.
- Large tool-research track: `docs/wiki/research/tool-technology-incorporation-roadmap.md` and related slice plans.
- Simplicity implementation history: `docs/wiki/research/redthread-simplicity-implementation-plan.md`.
- Wiki changelog: `docs/wiki/log.md`.
- Historical status: compact stubs at `docs/PROGRESS.md` and `docs/REDTHREAD_STATUS_AUDIT.md`; full copies live under `docs/archive/historical/`.

## Do Not Load By Default

- `docs/wiki/research/*` unless the task names that research track.
- `docs/wiki/log.md` unless auditing wiki history.
- Archived handoff or state notes unless the task asks for session continuity.
- Ignored local files such as `CODEX.md` and `direction.md`.
- `docs/archive/*` unless checking historical provenance.

## Agent Work Rules

- Use code and shell tools for deterministic facts. Use the model for judgment, synthesis, and summarization.
- Make surgical changes. Do not refactor adjacent code unless needed for the task.
- State conflicts instead of blending them. Pick the newer or more authoritative source and flag the other.
- Verify before saying done. If a check is skipped or fails, say so.
- Keep summaries short and linked to source files.

## Open Review Items

- `.agent/` and `.codex/` intentionally coexist. See `docs/context-index.md` for mirror policy.
- `CODEX.md` is ignored local guidance. Useful rules have been merged into `AGENTS.md` and this summary.
- Historical status docs now have compact stubs at the old paths and full copies in `docs/archive/historical/`.
