# RedThread Wiki Architecture

## Purpose

RedThread now uses a **two-layer knowledge system**:

1. **MemPalace** — machine-oriented memory and retrieval
2. **LLM Wiki** — human-browsable, LLM-maintained markdown knowledge base

This document explains how the two layers fit together so future sessions do not confuse raw evidence, recalled memory, and curated synthesis.

## The Knowledge Stack

### Layer 1 — Raw sources
Immutable source-of-truth inputs.

Examples:
- `docs/*.md`
- task artifacts
- transcripts
- research notes
- external markdown dropped into the repo

The agent may read these files, but must not silently rewrite them to fit a narrative.

### Layer 2 — MemPalace
Persistent retrieval layer.

Use MemPalace for:
- semantic search
- wake-up context
- durable memory across sessions
- person/project/topic recall
- diary-like session continuity

MemPalace answers: **"what have we seen before?"**

### Layer 3 — Wiki
Persistent synthesis layer under `docs/wiki/`.

Use the wiki for:
- concept pages
- entity pages
- system overviews
- decision records
- timelines
- research summaries
- open questions and contradictions

The wiki answers: **"what do we currently believe, and why?"**

### Layer 4 — Agent schema
Operating rules that keep the system coherent.

Primary files:
- `AGENTS.md`
- `docs/WIKI_ARCHITECTURE.md`
- `docs/WIKI_INGEST_WORKFLOW.md`
- `docs/wiki/SCHEMA.md`
- `docs/MEMPALACE_SETUP.md`

## Why both layers exist

MemPalace is strong at retrieval and continuity, but it is not itself a polished, human-facing knowledge base.

The wiki is strong at synthesis and navigation, but it should not become detached from evidence.

Using both gives us:
- recall from MemPalace
- durable synthesis from markdown pages
- better onboarding for humans
- less re-derivation by the LLM on repeated queries

## Operating model

### Ingest
When a new source arrives:
1. read the raw source
2. search MemPalace for related prior work
3. update or create relevant wiki pages
4. update `docs/wiki/index.md`
5. append a record to `docs/wiki/log.md`
6. optionally re-mine the changed wiki pages into MemPalace

### Query
When answering a substantial question:
1. inspect `docs/wiki/index.md`
2. read the most relevant wiki pages
3. verify uncertain or high-impact claims against raw sources and/or MemPalace
4. answer with citations
5. if the answer creates durable value, file it back into the wiki

### Lint
Periodically review the wiki for:
- stale claims
- contradictions
- orphan pages
- missing cross-references
- missing source citations
- concepts present in memory but absent from the wiki

## Guardrails

### Never collapse source and synthesis
A wiki page is not automatically source-of-truth just because it exists.

Every important page should distinguish:
- raw evidence
- derived summary
- active decision
- open question
- superseded claim

### Search before editing
Before changing a wiki page that touches architecture, evaluation, research, or memory behavior:
- inspect relevant source docs
- search MemPalace for related prior work
- check for existing wiki pages that already cover the topic

### Prefer additive edits over silent rewrites
If new information changes the story, record that change clearly.

Good patterns:
- add a "Superseded by" note
- add a contradiction section
- append timeline updates
- update decision status from `proposed` to `accepted` or `superseded`

## Recommended page families

- `docs/wiki/entities/` — named systems, tools, models, roles
- `docs/wiki/concepts/` — reusable ideas and mechanisms
- `docs/wiki/decisions/` — why a design choice exists
- `docs/wiki/systems/` — larger subsystem overviews
- `docs/wiki/research/` — topic investigations and synthesis
- `docs/wiki/timelines/` — phase and history tracking

## Relationship to existing docs

Existing docs under `docs/` remain the primary engineering references.

The wiki is a **curated companion layer**, not a replacement for:
- `docs/PHASE_REGISTRY.md`
- `docs/TECH_STACK.md`
- `docs/AGENT_ARCHITECTURE.md`
- `docs/ANTI_HALLUCINATION_SOP.md`

If a wiki page and a source-of-truth engineering doc disagree, resolve the disagreement explicitly instead of silently favoring the wiki.

## Minimal maintenance loop

For normal work in this repo, the minimum safe loop is:
1. read source docs
2. search MemPalace
3. update wiki page(s)
4. update index
5. append log entry

That is the baseline workflow all future sessions should follow.
