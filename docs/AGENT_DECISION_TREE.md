# Agent Decision Tree

Use this table before opening deeper context. All paths are repo-root relative and point to existing source-of-truth docs.

| Task Type | Primary Doc | Secondary Docs |
| :--- | :--- | :--- |
| General project overview / product positioning | `docs/product.md` | `README.md`, `docs/TECH_STACK.md` |
| Phase progression / roadmap / current status | `docs/PHASE_REGISTRY.md` | `docs/PROGRESS.md`, `docs/REDTHREAD_STATUS_AUDIT.md` |
| Attack algorithms | `docs/algorithms.md` | `docs/PHASE_REGISTRY.md` |
| Evaluation / JudgeAgent scoring | `docs/ANTI_HALLUCINATION_SOP.md` | `docs/algorithms.md`, `docs/PHASE_REGISTRY.md` |
| Defense synthesis / guardrails | `docs/DEFENSE_PIPELINE.md` | `docs/SELF_HEALING_HARDENING_PLAN.md`, `docs/PHASE_REGISTRY.md` |
| Agentic-security runtime / Phase 8 | `docs/AGENTIC_SECURITY_RUNTIME.md` | `docs/PRD_PHASE8_AGENTIC_SECURITY.md`, `docs/PHASE8_TESTING_GUIDE.md` |
| Agent/subagent operating architecture | `docs/AGENT_ARCHITECTURE.md` | `docs/RPI_METHODOLOGY.md`, `AGENTS.md` |
| Knowledge System / Memory / Wiki Maintenance | `docs/WIKI_ARCHITECTURE.md` | `docs/WIKI_INGEST_WORKFLOW.md`, `docs/wiki/SCHEMA.md`, `docs/wiki/index.md` |

## Source-of-truth order

1. Current product and architecture docs win over historical ledgers.
2. `docs/PHASE_REGISTRY.md` is the phase-status authority.
3. `docs/PROGRESS.md` and `docs/REDTHREAD_STATUS_AUDIT.md` are historical unless their header says otherwise.
4. `docs/wiki/` is a synthesis layer, not the engineering source of truth.
