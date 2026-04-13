# Wiki Schema

## Goal

This schema teaches the agent how to maintain `docs/wiki/` as a persistent, compounding knowledge base without confusing curated synthesis with raw evidence.

## Directory structure

```text
docs/wiki/
  index.md
  log.md
  SCHEMA.md
  entities/
  concepts/
  decisions/
  research/
  systems/
  timelines/
```

## Core rules

1. **The wiki is LLM-maintained.** Humans may edit it, but agents should assume responsibility for organization, cross-links, and upkeep.
2. **Raw source docs stay authoritative.** The wiki summarizes and connects; it does not silently replace source docs.
3. **High-impact claims require citations.** Architecture, evaluation, promotion, and safety claims should point to source docs.
4. **Every durable update touches both navigation files.** Update `index.md`; append to `log.md`.
5. **Prefer stable page names.** Avoid renaming pages unless there is a strong reason.

## Required frontmatter

Every substantive wiki page should start with YAML frontmatter like this:

```yaml
---
title: Knowledge Stack
type: system
status: active
summary: How MemPalace and the wiki work together in RedThread.
source_of_truth:
  - docs/WIKI_ARCHITECTURE.md
  - docs/MEMPALACE_SETUP.md
updated_by: codex
updated_at: 2026-04-13
---
```

## Page types

### `entity`
For a named tool, role, model, or subsystem actor.

Use when the page is primarily about **what a thing is**.

Suggested sections:
- What it is
- Responsibilities
- Interfaces
- Related pages
- Sources

### `concept`
For a reusable idea or design mechanism.

Use when the page explains **how an idea works**.

Suggested sections:
- Definition
- Why it matters
- How it appears in RedThread
- Related pages
- Sources

### `decision`
For an explicit design choice.

Use when the page explains **why we chose something**.

Suggested sections:
- Decision
- Context
- Consequences
- Alternatives considered
- Sources

Allowed statuses:
- `proposed`
- `accepted`
- `superseded`

### `system`
For a larger subsystem or cross-cutting architecture area.

Use when the page covers **multiple components together**.

Suggested sections:
- Scope
- Components
- Data flow or workflow
- Risks / open questions
- Sources

### `research`
For exploratory synthesis.

Use when the page tracks **current investigation state**.

Suggested sections:
- Research question
- Current synthesis
- Evidence
- Contradictions / uncertainty
- Next questions

### `timeline`
For historical evolution over time.

Use when sequence matters.

Suggested sections:
- Time-ordered milestones
- Changes in interpretation
- Current state
- Sources

## Citation rules

For claims that affect implementation or safety, cite one or more of:
- source docs in `docs/`
- task artifacts
- raw notes
- external sources if brought into the repo

When possible, use repo-relative links.

## Update workflows

### Ingest workflow
1. read new source
2. search MemPalace for related memory
3. decide which page families are affected
4. create or update wiki pages
5. update `index.md`
6. append to `log.md`
7. optionally re-mine affected pages into MemPalace

### Query-to-page workflow
If a user question yields durable insight:
1. answer the question
2. decide whether the answer deserves persistence
3. convert it into a wiki page or update an existing page
4. log the change

### Lint workflow
Check for:
- missing frontmatter
- missing citations
- orphan pages
- duplicate pages with overlapping scope
- stale decisions
- contradictions not explicitly tracked

## Navigation contract

### `index.md`
Content-oriented map.

Must include:
- page link
- one-line summary
- grouped sections by page family

### `log.md`
Chronological record.

Append-only format:

```md
## [2026-04-13] scaffold | initialized wiki
- created schema, index, log, and starter pages
- linked wiki architecture to MemPalace setup
```

## Naming rules

- use lowercase kebab-case filenames
- keep names semantic, not conversational
- prefer one clear topic per page
- if a page grows too broad, split it and add links between the new pages

## RedThread-specific guardrails

1. Be conservative with claims about `research`, `evaluation`, `telemetry`, and promotion/revalidation.
2. If a wiki claim is uncertain, mark it as uncertain instead of stating it as settled fact.
3. Do not mutate source-of-truth engineering docs just to make the wiki cleaner.
4. When a wiki page summarizes a roadmap or phase, link back to `docs/PHASE_REGISTRY.md`.

## Starter expectation for agents

Before editing `docs/wiki/`, agents should read:
- `docs/WIKI_ARCHITECTURE.md`
- `docs/wiki/SCHEMA.md`
- `docs/wiki/index.md`
- the specific source docs relevant to the topic
