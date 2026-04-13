# Wiki Index

This is the primary content map for the RedThread wiki.

## Systems

- [systems/knowledge-stack.md](systems/knowledge-stack.md) — How MemPalace, raw sources, and the wiki fit together.
- [systems/evaluation-and-anti-hallucination.md](systems/evaluation-and-anti-hallucination.md) — Evaluation baseline, grounded generation rules, and why anti-hallucination is treated as an engineering control.
- [systems/telemetry-and-monitoring.md](systems/telemetry-and-monitoring.md) — Drift detection, ASI, and continuous monitoring behavior.
- [systems/promotion-and-revalidation.md](systems/promotion-and-revalidation.md) — Promotion discipline, revalidation evidence, and why mutation execution is kept separate from acceptance.
- [systems/defense-synthesis-and-validation.md](systems/defense-synthesis-and-validation.md) — Self-healing path from confirmed jailbreak to validated defense proposal.

## Decisions

- [decisions/adopt-mempalace-plus-llm-wiki.md](decisions/adopt-mempalace-plus-llm-wiki.md) — Why RedThread uses MemPalace for retrieval and a markdown wiki for synthesis.

## Entities

- [entities/README.md](entities/README.md) — Index rules and scope for entity pages.
- [entities/mempalace.md](entities/mempalace.md) — Memory and retrieval layer used by the repo.
- [entities/judge-agent.md](entities/judge-agent.md) — Evaluation role responsible for scoring attack traces.
- [entities/defense-architect.md](entities/defense-architect.md) — Grounded defensive generation role in the self-healing loop.
- [entities/asi.md](entities/asi.md) — Composite Agent Stability Index used by telemetry.
- [entities/prometheus-2.md](entities/prometheus-2.md) — Evaluation model referenced in the grounded judging stack.
- [entities/langgraph-supervisor.md](entities/langgraph-supervisor.md) — Coordinator role for macro-workflow orchestration.

## Concepts

- [concepts/README.md](concepts/README.md) — Index rules and scope for concept pages.

## Research

- [research/README.md](research/README.md) — How to structure ongoing investigations.
- [research/bounded-autoresearch.md](research/bounded-autoresearch.md) — Current synthesis of bounded offense and defense mutation lanes.

## Timelines

- [timelines/README.md](timelines/README.md) — How to track history and roadmap evolution.
- [timelines/redthread-phase-evolution.md](timelines/redthread-phase-evolution.md) — High-level project evolution from PAIR foundation to bounded autoresearch.

## Workflow Docs

- [../WIKI_INGEST_WORKFLOW.md](../WIKI_INGEST_WORKFLOW.md) — Repeatable ingest procedure for source → wiki → index/log → lint → re-mine.
- [../WIKI_QUERY_TO_PAGE_WORKFLOW.md](../WIKI_QUERY_TO_PAGE_WORKFLOW.md) — Repeatable procedure for turning a strong chat answer into a durable wiki page.
- [../WIKI_MAINTENANCE_CHECKLIST.md](../WIKI_MAINTENANCE_CHECKLIST.md) — Daily operational checklist for safe wiki maintenance.

## Log

- [log.md](log.md) — Append-only history of wiki maintenance activity.
